package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.content.Intent;
import android.support.annotation.Nullable;

/**
 * Created by Alex on 2/27/2018.
 */

public class SocketService extends IntentService {

    public static final String WORKER_THREAD_NAME = "socket_worker";

    public SocketService() {
        super(WORKER_THREAD_NAME);
    }

    @Override
    protected void onHandleIntent(@Nullable Intent intent) {

    }
}
