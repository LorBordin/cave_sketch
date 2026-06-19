package com.cavesketch.app.bridge

interface SurveyBridge {
    /** Calls survey_bridge.generate_survey_plot; returns its JSON result string. */
    suspend fun generate(inputsJson: String, workDir: String): String
}
