import MorerduoKit
import SwiftUI

struct ListeningSettingsView: View {
  @ObservedObject var viewModel: AppViewModel

  var body: some View {
    HStack(alignment: .top, spacing: 28) {
      speedSetting
      Divider()
      timerSetting
    }
    .padding(18)
    .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 12))
  }

  private var speedSetting: some View {
    VStack(alignment: .leading, spacing: 10) {
      Text("朗读速度")
        .font(.headline)
      Picker("朗读速度", selection: speedBinding) {
        Text("慢").tag(ReadingSpeed.slow)
        Text("正常").tag(ReadingSpeed.normal)
        Text("快").tag(ReadingSpeed.fast)
      }
      .labelsHidden()
      .pickerStyle(.segmented)
      .accessibilityLabel("朗读速度")
      .accessibilityIdentifier(AppAccessibilityIdentifiers.speedPicker)
      .disabled(!viewModel.state.canEditSpeed)
      Text("播放时不可更改；暂停后可调整。")
        .font(.caption)
        .foregroundStyle(.secondary)
    }
    .frame(maxWidth: .infinity, alignment: .leading)
  }

  private var timerSetting: some View {
    VStack(alignment: .leading, spacing: 10) {
      Text("定时停止")
        .font(.headline)
      HStack {
        TextField("1–240", text: $viewModel.timerInput)
          .frame(width: 90)
          .textFieldStyle(.roundedBorder)
          .onSubmit { viewModel.validateTimerInput() }
          .accessibilityLabel("定时分钟数，留空表示不限时")
          .accessibilityIdentifier(AppAccessibilityIdentifiers.timerMinutesField)
          .disabled(!viewModel.state.canEditTimer)
        Text("分钟")
          .foregroundStyle(.secondary)
      }
      if let message = viewModel.timerValidationMessage {
        Text(message)
          .font(.caption)
          .foregroundStyle(.red)
          .fixedSize(horizontal: false, vertical: true)
          .accessibilityIdentifier(
            AppAccessibilityIdentifiers.timerValidationMessage
          )
      } else {
        Text("留空不限时，只累计实际朗读时间。")
          .font(.caption)
          .foregroundStyle(.secondary)
      }
    }
    .frame(maxWidth: .infinity, alignment: .leading)
  }

  private var speedBinding: Binding<ReadingSpeed> {
    Binding(
      get: { viewModel.state.speed },
      set: { viewModel.changeSpeed($0) }
    )
  }
}
