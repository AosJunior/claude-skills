// Máscara da pessoa com o Apple Vision, quadro a quadro. É um filtro: lê quadros BGRA crus pela entrada padrão
// e escreve quadros cinza crus (0 = fundo, 255 = pessoa, faixa completa) na saída padrão. Quem decodifica e
// codifica é o mascara.py, com o ffmpeg do PATH; aqui não há caminho fixo nem arquivo.
//
// Uso: mascara_vision <largura> <altura>
// Pessoa: VNGeneratePersonSegmentationRequest(.accurate), subida para a resolução do vídeo com upsample guiado
// pela imagem (preserva fio de cabelo). No macOS 14 ou mais novo, une com VNGenerateForegroundInstanceMaskRequest
// (roupa, objeto na mão). Depois: borda suavizada, mediana de 3 quadros (tira estalo de um quadro só) e
// suavização no tempo onde a máscara quase não mudou.
// Ajustes finos por variável de ambiente: ALPHA, FEATHER, SIGMA, LUMA, INST (0 = só pessoa), GATER, MOTIONT,
// MEDIAN3, LVLO, LVHI.

import Accelerate
import CoreImage
import CoreVideo
import Foundation
import Vision

func falhar(_ msg: String) -> Never {
    FileHandle.standardError.write("mascara_vision: \(msg)\n".data(using: .utf8)!)
    exit(2)
}

let args = CommandLine.arguments
guard args.count == 3, let W = Int(args[1]), let H = Int(args[2]), W > 0, H > 0 else {
    falhar("uso: mascara_vision <largura> <altura>")
}
let env = ProcessInfo.processInfo.environment
func num(_ k: String, _ padrao: Double) -> Double { Double(env[k] ?? "") ?? padrao }
let alpha = Float(num("ALPHA", 0.65))
let feather = num("FEATHER", 1.5)
let sigma = num("SIGMA", 3.0)
let lumaSigma = num("LUMA", 0.10)
let gateR = num("GATER", 45)
let motionT = Float(num("MOTIONT", 60))
let median3 = (env["MEDIAN3"] ?? "1") == "1"
let lvLo = Float(num("LVLO", 0.06)), lvHi = Float(num("LVHI", 0.94))
var useInst = (env["INST"] ?? "1") == "1"
if useInst {
    if #available(macOS 14.0, *) {} else {
        FileHandle.standardError.write("mascara_vision: macOS anterior ao 14, só a pessoa (sem objetos na mão)\n".data(using: .utf8)!)
        useInst = false
    }
}

let N = W * H
let entrada = FileHandle.standardInput
let saida = FileHandle.standardOutput
let ctx = CIContext(options: [.workingColorSpace: NSNull(), .outputColorSpace: NSNull(), .cacheIntermediates: false])
let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
let seq = VNSequenceRequestHandler()

var pb: CVPixelBuffer?
let attrs = [kCVPixelBufferIOSurfacePropertiesKey as String: [String: Any]()] as CFDictionary
guard CVPixelBufferCreate(kCFAllocatorDefault, W, H, kCVPixelFormatType_32BGRA, attrs, &pb) == kCVReturnSuccess,
      let quadro = pb else { falhar("não consegui criar o buffer de \(W)x\(H)") }

var cur = [UInt8](repeating: 0, count: N)
var tmpB = [UInt8](repeating: 0, count: N)
var curF = [Float](repeating: 0, count: N)
var prevF = [Float](repeating: 0, count: N)
var outB = [UInt8](repeating: 0, count: N)
var mA = [UInt8](repeating: 0, count: N), mB = [UInt8](repeating: 0, count: N), medB = [UInt8](repeating: 0, count: N)
var first = true
var rawCount = 0

// lê exatamente um quadro BGRA; false no fim da entrada
func lerQuadro() -> Bool {
    let bytesLinha = W * 4
    var dados = Data()
    dados.reserveCapacity(N * 4)
    while dados.count < N * 4 {
        let d = entrada.readData(ofLength: N * 4 - dados.count)
        if d.isEmpty { return false }
        dados.append(d)
    }
    CVPixelBufferLockBaseAddress(quadro, [])
    let base = CVPixelBufferGetBaseAddress(quadro)!
    let passo = CVPixelBufferGetBytesPerRow(quadro)
    dados.withUnsafeBytes { src in
        for y in 0..<H {
            memcpy(base + y * passo, src.baseAddress! + y * bytesLinha, bytesLinha)
        }
    }
    CVPixelBufferUnlockBaseAddress(quadro, [])
    return true
}

// suavização no tempo + níveis + escrita de um quadro
func emitir(_ buf: [UInt8]) {
    vDSP_vfltu8(buf, 1, &curF, 1, vDSP_Length(N))
    if first {
        prevF = curF
        first = false
    } else {
        let b0 = 1 - alpha
        curF.withUnsafeBufferPointer { c in
            prevF.withUnsafeMutableBufferPointer { p in
                for i in 0..<N {
                    let d = abs(c[i] - p[i])
                    let wPrev = d >= motionT ? 0 : b0 * (1 - d / motionT)
                    p[i] = c[i] + wPrev * (p[i] - c[i])
                }
            }
        }
    }
    var sc = 1 / (lvHi - lvLo), of = -lvLo * 255 / (lvHi - lvLo)
    vDSP_vsmsa(prevF, 1, &sc, &of, &curF, 1, vDSP_Length(N))
    var lo: Float = 0, hi: Float = 255
    vDSP_vclip(curF, 1, &lo, &hi, &curF, 1, vDSP_Length(N))
    vDSP_vfixru8(curF, 1, &outB, 1, vDSP_Length(N))
    outB.withUnsafeBytes { saida.write(Data($0)) }
}

while lerQuadro() {
    var ok = true
    autoreleasepool {
        do {
            try seq.perform([req], on: quadro, orientation: .up)
        } catch {
            FileHandle.standardError.write("mascara_vision: o Vision falhou num quadro (\(error)); repito a máscara anterior\n".data(using: .utf8)!)
            ok = false
            return
        }
        guard let mpb = req.results?.first?.pixelBuffer else { ok = false; return }
        let img = CIImage(cvPixelBuffer: quadro)
        var m = CIImage(cvPixelBuffer: mpb)
        let up = CIFilter(name: "CIEdgePreserveUpsampleFilter")!
        up.setValue(img, forKey: kCIInputImageKey)
        up.setValue(m, forKey: "inputSmallImage")
        up.setValue(sigma, forKey: "inputSpatialSigma")
        up.setValue(lumaSigma, forKey: "inputLumaSigma")
        m = up.outputImage!.cropped(to: img.extent)
        if useInst, #available(macOS 14.0, *) {
            let instReq = VNGenerateForegroundInstanceMaskRequest()
            let h = VNImageRequestHandler(cvPixelBuffer: quadro, orientation: .up)
            if (try? h.perform([instReq])) != nil, let r = instReq.results?.first, !r.allInstances.isEmpty,
               let ipb = try? r.generateScaledMaskForImage(forInstances: r.allInstances, from: h) {
                var inst = CIImage(cvPixelBuffer: ipb)
                let sx = img.extent.width / inst.extent.width, sy = img.extent.height / inst.extent.height
                if abs(sx - 1) > 0.001 || abs(sy - 1) > 0.001 { inst = inst.transformed(by: CGAffineTransform(scaleX: sx, y: sy)) }
                inst = inst.clampedToExtent().applyingGaussianBlur(sigma: 1.0).cropped(to: img.extent)
                // a pessoa só vale perto do que o detector de primeiro plano marcou (corta manchas soltas)
                let idl = inst.clampedToExtent().applyingFilter("CIMorphologyMaximum", parameters: ["inputRadius": gateR])
                    .applyingGaussianBlur(sigma: gateR / 3).cropped(to: img.extent)
                let gated = m.applyingFilter("CIMultiplyCompositing", parameters: [kCIInputBackgroundImageKey: idl])
                m = inst.applyingFilter("CIMaximumCompositing", parameters: [kCIInputBackgroundImageKey: gated]).cropped(to: img.extent)
            }
        }
        cur.withUnsafeMutableBytes { p in
            ctx.render(m, toBitmap: p.baseAddress!, rowBytes: W, bounds: img.extent, format: .L8, colorSpace: nil)
        }
    }
    if !ok && rawCount == 0 { cur = [UInt8](repeating: 0, count: N) }   // sem máscara anterior: quadro vazio
    if feather > 0 {
        let k = UInt32(2 * Int((feather * 1.5).rounded()) + 1)
        cur.withUnsafeMutableBytes { c in
            tmpB.withUnsafeMutableBytes { t in
                var src = vImage_Buffer(data: c.baseAddress!, height: vImagePixelCount(H), width: vImagePixelCount(W), rowBytes: W)
                var dst = vImage_Buffer(data: t.baseAddress!, height: vImagePixelCount(H), width: vImagePixelCount(W), rowBytes: W)
                vImageTentConvolve_Planar8(&src, &dst, nil, 0, 0, k, k, 0, vImage_Flags(kvImageEdgeExtend))
            }
        }
        swap(&cur, &tmpB)
    }
    // mediana de 3 quadros: o quadro k-1 sai como mediana(k-2, k-1, k); sai o mesmo número de quadros que entrou
    if !median3 { emitir(cur); rawCount += 1; continue }
    if rawCount == 0 {
        mA = cur; mB = cur
    } else {
        if rawCount == 1 { emitir(mB) } else {
            mA.withUnsafeBufferPointer { a in mB.withUnsafeBufferPointer { b in cur.withUnsafeBufferPointer { c in
                medB.withUnsafeMutableBufferPointer { o in
                    for i in 0..<N {
                        let x = a[i], y = b[i], z = c[i]
                        o[i] = max(min(x, y), min(max(x, y), z))
                    }
                }
            }}}
            emitir(medB)
        }
        swap(&mA, &mB); mB = cur
    }
    rawCount += 1
}
if median3 && rawCount > 0 { emitir(mB) }
