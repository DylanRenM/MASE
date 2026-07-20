public struct AppViewState: Equatable, Sendable {
  public let mode: SessionMode
  public let statusText: String
  public let fileName: String
  public let progressFraction: Double
  public let progressText: String
  public let playPauseTitle: String
  public let canChooseFile: Bool
  public let canPlayPause: Bool
  public let canStop: Bool
  public let canEditSpeed: Bool
  public let canEditTimer: Bool
  public let isLoading: Bool
  public let isReloadPromptPresented: Bool
  public let reloadPromptToken: ReloadPromptToken?
  public let errorMessage: String?
  public let speed: ReadingSpeed

  public init(session: ReadingSessionState) throws {
    let metadata = try session.document.map {
      try ParagraphProgressMetadata(lengths: $0.paragraphs.map(\.utf16Length))
    }
    let progress = try ProgressCalculator.progress(
      metadata: metadata,
      cursor: session.cursor
    )
    mode = session.mode
    statusText = Self.statusText(for: session.mode)
    fileName = session.document?.name ?? "尚未选择文件"
    progressFraction = progress.fraction
    progressText = Self.progressText(progress)
    playPauseTitle = Self.playPauseTitle(for: session.mode)
    canChooseFile = ![.loading, .awaitingReloadDecision].contains(session.mode)
    canPlayPause = [.ready, .playing, .paused].contains(session.mode)
    canStop = [.playing, .paused].contains(session.mode)
    canEditSpeed = [.idle, .ready, .paused].contains(session.mode)
    canEditTimer = [.idle, .ready].contains(session.mode)
    isLoading = session.mode == .loading
    isReloadPromptPresented = session.mode == .awaitingReloadDecision
    reloadPromptToken = session.reloadPromptToken
    errorMessage = session.error.map(AppErrorMessageMapper.message)
    speed = session.speed
  }

  private static func statusText(for mode: SessionMode) -> String {
    switch mode {
    case .idle:
      return "等待选择文件"
    case .loading:
      return "正在载入文件"
    case .ready:
      return "文件已就绪"
    case .playing:
      return "正在朗读"
    case .paused:
      return "已暂停"
    case .awaitingReloadDecision:
      return "等待处理源文件变化"
    }
  }

  private static func playPauseTitle(for mode: SessionMode) -> String {
    switch mode {
    case .playing:
      return "暂停"
    case .paused:
      return "继续"
    case .idle, .loading, .ready, .awaitingReloadDecision:
      return "播放"
    }
  }

  private static func progressText(_ progress: ReadingProgress) -> String {
    let percentage = Int((progress.fraction * 100).rounded())
    return "\(percentage)% · \(progress.currentParagraph) / \(progress.totalParagraphs) 段"
  }
}
