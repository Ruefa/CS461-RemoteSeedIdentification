package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Binder;
import android.os.IBinder;
import android.support.annotation.Nullable;
import android.util.Log;

/**
 * Created by Alex on 2/27/2018.
 */

public class SocketService extends IntentService {

    public static final String WORKER_THREAD_NAME = "socket_worker";
    private static final String TAG = "SocketService";

    public ServerUtils mServer;
    private final IBinder mBinder = new SocketBinder();

    public SocketService() {
        super(WORKER_THREAD_NAME);
    }

    public class SocketBinder extends Binder {
        SocketService getService() {
            return SocketService.this;
        }
    }

    @Override
    protected void onHandleIntent(@Nullable Intent intent) {
        try {
            Log.d("Server: ", "about to begin");
            mServer = new ServerUtils(new ServerUtils.MessageCallback() {
                @Override
                public void callbackMessageReceiver(String message) {
                    Log.d("Server message: ", message);
                }
            }, this);
        } catch (NullPointerException e) {
            e.printStackTrace();
        }
        mServer.openSocket();
    }

    /*@Override
    public int onStartCommand(Intent intent, int flags, int startId){
        openSocket();

        return START_STICKY;
    }*/

    @Override
    public IBinder onBind(Intent intent){
        return mBinder;
    }
}
