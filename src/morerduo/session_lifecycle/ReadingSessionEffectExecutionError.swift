public enum ReadingSessionEffectExecutionError: Error, Equatable, Sendable {
  case userFacing(UserFacingError)
}
