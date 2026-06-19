package com.cavesketch.app.bridge

import com.chaquo.python.Python
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

class PythonBridge(private val io: CoroutineDispatcher) : SurveyBridge {
    override suspend fun generate(inputsJson: String, workDir: String): String =
        withContext(io) {
            Python.getInstance()
                .getModule("survey_bridge")
                .callAttr("generate_survey_plot", inputsJson, workDir)
                .toString()
        }
}
