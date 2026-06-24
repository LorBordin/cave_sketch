package com.cavesketch.app

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Lifecycle of the on-device Python runtime startup. */
sealed interface InitStatus {
    data object Initializing : InitStatus
    data object Ready : InitStatus
    data class Failed(val message: String) : InitStatus
}

/** Observable holder for the app's one-time initialization status. */
class AppInitState {
    private val _status = MutableStateFlow<InitStatus>(InitStatus.Initializing)
    val status: StateFlow<InitStatus> = _status.asStateFlow()

    fun markReady() { _status.value = InitStatus.Ready }
    fun markFailed(message: String) { _status.value = InitStatus.Failed(message) }
}
