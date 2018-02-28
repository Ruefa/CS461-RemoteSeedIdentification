package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;
import android.support.annotation.Nullable;
import android.util.Log;

/**
 * Created by Alex on 2/27/2018.
 */

public class SocketService extends IntentService {

    public static final String WORKER_THREAD_NAME = "socket_worker";

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
        if(mServer == null) {
            try {
                Log.d("Server: ", "about to begin");
                mServer = new ServerUtils(new ServerUtils.MessageCallback() {
                    @Override
                    public void callbackMessageReceiver(String message) {
                        Log.d("Server message: ", message);
                    }
                });
            } catch (NullPointerException e) {
                e.printStackTrace();
            }
            mServer.openSocket();
        }else{
            mServer.sendMessage("test");
        }
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

    private void openSocket(){
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
