// Immagini del sito: anteprime di condivisione 1200×630 in JPEG (assets/og) a partire da _build/og_spec.json
// e dalle icone dell'app. Uso, dalla cartella Website: swift _build/make_images.swift
import AppKit
import CoreGraphics

let site = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let assets = site.deletingLastPathComponent().appendingPathComponent("Widgetfeste/Assets.xcassets")
let outDir = site.appendingPathComponent("assets/og")
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

struct Spec: Decodable { let id: String; let title: String; let colors: [String]; let accent: String; let icon: String }
let specs = try! JSONDecoder().decode([Spec].self, from: Data(contentsOf: site.appendingPathComponent("_build/og_spec.json")))

func color(_ hex: String, _ a: CGFloat = 1) -> NSColor {
    let v = Int(hex.dropFirst(), radix: 16)!
    return NSColor(srgbRed: CGFloat(v >> 16) / 255, green: CGFloat((v >> 8) & 255) / 255, blue: CGFloat(v & 255) / 255, alpha: a)
}

func hash(_ i: Int, _ salt: Int) -> CGFloat {
    let x = sin(Double(i) * 127.1 + Double(salt) * 311.7) * 43758.5453
    return CGFloat(x - floor(x))
}

func iconImage(_ name: String) -> NSImage {
    let path = name == "Default"
        ? assets.appendingPathComponent("AppIcon.appiconset/AppIcon.png")
        : assets.appendingPathComponent("AppIcon-\(name).appiconset/AppIcon-\(name).png")
    return NSImage(contentsOf: path)!
}

func font(_ size: CGFloat, weight: NSFont.Weight, design: NSFontDescriptor.SystemDesign) -> NSFont {
    let base = NSFont.systemFont(ofSize: size, weight: weight)
    return NSFont(descriptor: base.fontDescriptor.withDesign(design) ?? base.fontDescriptor, size: size) ?? base
}

let W: CGFloat = 1200, H: CGFloat = 630

for spec in specs {
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(W), pixelsHigh: Int(H), bitsPerSample: 8, samplesPerPixel: 4,
                               hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    let gc = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.current = gc
    let ctx = gc.cgContext

    // Sfondo: gradiente della festa, alone e stelline
    NSGradient(colors: spec.colors.map { color($0) })!.draw(in: NSRect(x: 0, y: 0, width: W, height: H), angle: -55)
    NSGradient(colors: [NSColor.black.withAlphaComponent(0.45), NSColor.black.withAlphaComponent(0)])!
        .draw(in: NSRect(x: 0, y: 0, width: W * 0.75, height: H), angle: 0)
    let glow = NSGradient(colors: [color(spec.accent, 0.35), color(spec.accent, 0)])!
    glow.draw(fromCenter: NSPoint(x: 930, y: 315), radius: 0, toCenter: NSPoint(x: 930, y: 315), radius: 360, options: [])
    for i in 0..<140 {
        let r = 0.8 + hash(i, 5) * 2.4
        color("#FFFAF2", 0.25 + hash(i, 4) * 0.55).setFill()
        NSBezierPath(ovalIn: NSRect(x: hash(i, 1) * W, y: hash(i, 2) * H, width: r * 2, height: r * 2)).fill()
    }

    // Icona con angoli arrotondati e ombra
    let side: CGFloat = 360
    let iconRect = NSRect(x: 930 - side / 2, y: 315 - side / 2, width: side, height: side)
    ctx.saveGState()
    ctx.setShadow(offset: CGSize(width: 0, height: -24), blur: 60, color: NSColor.black.withAlphaComponent(0.55).cgColor)
    NSColor.black.setFill()
    NSBezierPath(roundedRect: iconRect, xRadius: side * 0.225, yRadius: side * 0.225).fill()
    ctx.restoreGState()
    ctx.saveGState()
    NSBezierPath(roundedRect: iconRect, xRadius: side * 0.225, yRadius: side * 0.225).addClip()
    iconImage(spec.icon).draw(in: iconRect)
    ctx.restoreGState()

    // Marchio
    let brand = NSAttributedString(string: "QUANTO MANCA", attributes: [
        .font: font(26, weight: .heavy, design: .rounded), .foregroundColor: color(spec.accent), .kern: 4,
    ])
    brand.draw(at: NSPoint(x: 80, y: 520))

    // Titolo, rimpicciolito finché sta nella colonna di sinistra
    var size: CGFloat = 92
    var title: NSAttributedString
    repeat {
        let p = NSMutableParagraphStyle(); p.lineSpacing = -size * 0.08
        title = NSAttributedString(string: spec.title, attributes: [
            .font: font(size, weight: .heavy, design: .serif), .foregroundColor: color("#FFFAF2"), .paragraphStyle: p,
        ])
        size -= 2
    } while title.boundingRect(with: NSSize(width: 10_000, height: 1000), options: [.usesLineFragmentOrigin]).width > 640
    let tb = title.boundingRect(with: NSSize(width: 680, height: 1000), options: [.usesLineFragmentOrigin])
    title.draw(with: NSRect(x: 76, y: 300 - tb.height / 2 + 20, width: 680, height: tb.height), options: [.usesLineFragmentOrigin])

    let sub = NSAttributedString(string: "Countdown live, sfondi animati e widget per iPhone", attributes: [
        .font: font(28, weight: .semibold, design: .rounded), .foregroundColor: color("#FFFAF2", 0.82),
    ])
    sub.draw(at: NSPoint(x: 80, y: 90))
    let url = NSAttributedString(string: "quantomanca.github.io", attributes: [
        .font: font(22, weight: .bold, design: .rounded), .foregroundColor: color("#FFFAF2", 0.55),
    ])
    url.draw(at: NSPoint(x: 80, y: 48))

    NSGraphicsContext.restoreGraphicsState()
    let out = outDir.appendingPathComponent("\(spec.id).jpg")
    try! rep.representation(using: .jpeg, properties: [.compressionFactor: 0.82])!.write(to: out)
    print("✓ assets/og/\(spec.id).jpg")
}
