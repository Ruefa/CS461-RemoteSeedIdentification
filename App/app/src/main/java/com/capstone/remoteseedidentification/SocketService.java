package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.content.Intent;
import android.support.annotation.Nullable;
import android.util.Log;

/**
 * Created by Alex on 2/27/2018.
 */

public class SocketService extends IntentService {

    public static final String WORKER_THREAD_NAME = "socket_worker";

    private ServerUtils mServer;

    public SocketService() {
        super(WORKER_THREAD_NAME);
    }

    @Override
    protected void onHandleIntent(@Nullable Intent intent) {
        try{
            Log.d("Server: ", "about to begin");
            mServer = new ServerUtils(new ServerUtils.MessageCallback() {
                @Override
                public void callbackMessageReceiver(String message) {
                    Log.d("Server message: ", message);
                }
            });
        } catch (NullPointerException e){
            e.printStackTrace();
        }
        mServer.openSocket();
    }
}
