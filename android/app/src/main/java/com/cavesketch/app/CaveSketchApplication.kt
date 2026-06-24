package com.cavesketch.app

import android.app.Application
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class CaveSketchApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        // Per-session cleanup: remove last run's intermediate + output files.
        val present = filesDir.list()?.toList() ?: emptyList()
        com.cavesketch.app.util.filesToDelete(present).forEach {
            java.io.File(filesDir, it).delete()
        }

        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        // Pre-warm: pay the one-time heavy import + matplotlib font-cache cost off
        // the critical path (Phase 1 measurement strategy). Harmless if cheap.
        Thread {
            try {
                Python.getInstance().getModule("survey_bridge").callAttr("prewarm")
            } catch (_: Throwable) { /* best-effort warm-up */ }
        }.start()
    }
}
