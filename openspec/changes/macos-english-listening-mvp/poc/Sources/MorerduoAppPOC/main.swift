import AppKit
import SwiftUI

@main
struct MorerduoAppPOC: App {
    init() {
        NSApplication.shared.setActivationPolicy(.regular)
        DispatchQueue.main.async {
            NSApplication.shared.activate(ignoringOtherApps: true)
        }
    }

    var body: some Scene {
        WindowGroup("磨耳朵 POC") {
            AppPOCView()
        }
        .windowResizability(.contentSize)
    }
}

private struct AppPOCView: View {
    @State private var state = "等待选择文件"
    @State private var hasDocument = false
    @State private var isPlaying = false

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("磨耳朵")
                .font(.largeTitle.bold())
                .accessibilityIdentifier("appTitle")

            Text(state)
                .foregroundStyle(.secondary)
                .accessibilityIdentifier("sessionStatus")

            ProgressView(value: isPlaying ? 0.25 : 0)
                .accessibilityIdentifier("readingProgress")

            HStack {
                Button("载入示例") {
                    hasDocument = true
                    isPlaying = false
                    state = "文件已就绪"
                }
                .accessibilityLabel("载入示例")
                .accessibilityIdentifier("loadSampleButton")

                Button(isPlaying ? "暂停" : "播放") {
                    isPlaying.toggle()
                    state = isPlaying ? "正在朗读" : "已暂停"
                }
                .disabled(!hasDocument)
                .accessibilityLabel(isPlaying ? "暂停" : "播放")
                .accessibilityIdentifier("playPauseButton")

                Button("停止") {
                    isPlaying = false
                    state = "文件已就绪"
                }
                .disabled(!hasDocument)
                .accessibilityLabel("停止")
                .accessibilityIdentifier("stopButton")
            }
        }
        .padding(32)
        .frame(width: 440)
    }
}
