// macOS helper: capture only FleetLens's loopback web app in an offscreen WebKit view.
// Run while `python -m fleetlens.demo` serves http://127.0.0.1:5173/.
import AppKit
import AVFoundation
import CoreVideo
import WebKit

let output = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? "reports/m1-demo-2026-10-01.mp4")
let width = 1280
let height = 720
let fps: Int32 = 10
let application = NSApplication.shared
application.setActivationPolicy(.prohibited)
let webView = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: height))

func pump(until condition: () -> Bool, timeout: TimeInterval = 15) throws {
    let deadline = Date().addingTimeInterval(timeout)
    while !condition() && Date() < deadline {
        RunLoop.current.run(until: Date().addingTimeInterval(0.05))
    }
    if !condition() { throw NSError(domain: "FleetLensDemo", code: 1, userInfo: [NSLocalizedDescriptionKey: "Timed out waiting for local explorer"]) }
}

func js(_ code: String) throws -> Any? {
    var finished = false
    var value: Any?
    var failure: Error?
    webView.evaluateJavaScript(code) { result, error in
        value = result
        failure = error
        finished = true
    }
    try pump(until: { finished })
    if let failure { throw failure }
    return value
}

func snapshot() throws -> CGImage {
    var finished = false
    var value: NSImage?
    var failure: Error?
    webView.takeSnapshot(with: nil) { result, error in
        value = result
        failure = error
        finished = true
    }
    try pump(until: { finished })
    if let failure { throw failure }
    guard let image = value,
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        throw NSError(domain: "FleetLensDemo", code: 2, userInfo: [NSLocalizedDescriptionKey: "WebKit returned no image"])
    }
    return cgImage
}

func waitFor(_ expression: String) throws {
    let deadline = Date().addingTimeInterval(15)
    while Date() < deadline {
        if (try js(expression) as? Bool) == true { return }
        RunLoop.current.run(until: Date().addingTimeInterval(0.15))
    }
    throw NSError(domain: "FleetLensDemo", code: 3, userInfo: [NSLocalizedDescriptionKey: "Explorer did not show: \(expression)"])
}

func scene(_ caption: String, scroll: Int) throws -> CGImage {
    let safeCaption = String(data: try JSONSerialization.data(withJSONObject: [caption], options: [.fragmentsAllowed]), encoding: .utf8)!
    _ = try js("""
      (() => {
        let box = document.getElementById('m1-recording-caption');
        if (!box) {
          box = document.createElement('div'); box.id = 'm1-recording-caption';
          box.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#101923ee;color:#fff;padding:14px 28px;font:600 20px -apple-system,sans-serif;box-shadow:0 -3px 12px #0004';
          document.body.appendChild(box);
        }
        box.textContent = \(safeCaption)[0];
        window.scrollTo(0, \(scroll));
      })()
    """)
    RunLoop.current.run(until: Date().addingTimeInterval(0.5))
    return try snapshot()
}

do {
    let url = URL(string: "http://127.0.0.1:5173/")!
    webView.load(URLRequest(url: url))
    try waitFor("document.querySelector('.metrics-grid') !== null && document.querySelector('.detail-grid') !== null")

    let captures: [(CGImage, Int)] = [
        (try scene("M1 • Synthetic fixture • 11 logical samples, one event, 66 m valid distance", scroll: 250), 8),
        (try scene("Cohort rate = one episode ÷ 66 m × 100 km; vehicle strata keep their own denominators", scroll: 670), 9),
        (try scene("Fixture-brake • event window [1, 3) and eligible distance are visible together", scroll: 1020), 9),
        (try scene("Source lineage • the episode traces to sample sequences #1, #2, #3", scroll: 1450), 9),
    ]
    _ = try js("document.querySelectorAll('.drive-item')[1].click()")
    try waitFor("document.querySelector('.drive-context')?.textContent?.includes('fixture-gap') === true")
    let finalCapture = try scene("Fixture-gap • the excluded [2, 5) interval adds no valid distance or event", scroll: 1010)

    try? FileManager.default.removeItem(at: output)
    let writer = try AVAssetWriter(outputURL: output, fileType: .mp4)
    let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
        AVVideoCodecKey: AVVideoCodecType.h264,
        AVVideoWidthKey: width,
        AVVideoHeightKey: height,
        AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 2_000_000],
    ])
    input.expectsMediaDataInRealTime = false
    let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
        kCVPixelBufferWidthKey as String: width,
        kCVPixelBufferHeightKey as String: height,
        kCVPixelBufferIOSurfacePropertiesKey as String: [:],
    ])
    writer.add(input)
    guard writer.startWriting() else { throw writer.error ?? NSError(domain: "FleetLensDemo", code: 4) }
    writer.startSession(atSourceTime: .zero)
    var frame: Int64 = 0
    for (image, seconds) in captures + [(finalCapture, 10)] {
        for _ in 0..<(seconds * Int(fps)) {
            while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.01) }
            var pixelBuffer: CVPixelBuffer?
            let status = CVPixelBufferCreate(kCFAllocatorDefault, width, height, kCVPixelFormatType_32BGRA, nil, &pixelBuffer)
            guard status == kCVReturnSuccess, let buffer = pixelBuffer else { throw NSError(domain: "FleetLensDemo", code: 5) }
            CVPixelBufferLockBaseAddress(buffer, [])
            let context = CGContext(
                data: CVPixelBufferGetBaseAddress(buffer), width: width, height: height,
                bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue
            )!
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
            CVPixelBufferUnlockBaseAddress(buffer, [])
            guard adaptor.append(buffer, withPresentationTime: CMTime(value: frame, timescale: fps)) else {
                throw writer.error ?? NSError(domain: "FleetLensDemo", code: 6)
            }
            frame += 1
        }
    }
    input.markAsFinished()
    var finished = false
    writer.finishWriting { finished = true }
    try pump(until: { finished }, timeout: 60)
    guard writer.status == .completed else { throw writer.error ?? NSError(domain: "FleetLensDemo", code: 7) }
    print("Wrote \(output.path) (\(Double(frame) / Double(fps)) s, \(width)×\(height), silent)")
} catch {
    fputs("M1 recording failed: \(error)\n", stderr)
    exit(1)
}
