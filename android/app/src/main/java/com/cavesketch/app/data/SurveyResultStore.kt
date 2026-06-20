package com.cavesketch.app.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** The effective cave-map CSV produced by the Survey Plot screen, shared with the
 * Satellite Map screen (the reactive analog of the web app's session map_csv). */
data class SurveyResult(val mapCsvPath: String, val surveyName: String)

class SurveyResultStore {
    private val _result = MutableStateFlow<SurveyResult?>(null)
    val result: StateFlow<SurveyResult?> = _result.asStateFlow()

    fun publish(result: SurveyResult) {
        _result.value = result
    }
}
