package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Binder;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.support.annotation.Nullable;
import android.support.v4.content.LocalBroadcastManager;
import android.util.Log;
import android.os.Process;

/**
 * Created by Alex on 2/27/2018.
 */

public class SocketService extends Service {

    public static final String WORKER_THREAD_NAME = "socket_worker";
    private static final String TAG = "SocketService";

    public ServerUtils mServer;
    private final IBinder mBinder = new SocketBinder();

    private Looper mServiceLooper;
    private ServiceHandler mServiceHandler;
    private Context mContext;

    private final class ServiceHandler extends Handler {
        public ServiceHandler(Looper looper){
            super(looper);
        }

        public void handleMessage(Message message){
            Log.d(TAG, "handling message");

            mServer.mInitMessage = (String) message.obj;
            if(!mServer.mRun) {
                Log.d(TAG, "open socket");
                mServer.openSocket();
            }

            mServer.sendMessage((String) message.obj);

            String incomingMessage = mServer.receiveMessage();

            Intent intent = new Intent(LoginController.BROADCAST_ACTION);
            intent.putExtra("message", incomingMessage);
            LocalBroadcastManager.getInstance(mContext).sendBroadcast(intent);

            stopSelf(message.arg1);
        }
    }

    /*public SocketService() {
        super(WORKER_THREAD_NAME);
    }*/

    @Override
    public void onCreate() {
        HandlerThread thread = new HandlerThread("ServiceStartArguments",
                Process.THREAD_PRIORITY_BACKGROUND);
        thread.start();

        mServiceLooper = thread.getLooper();
        mServiceHandler = new ServiceHandler(mServiceLooper);

        Log.d(TAG, "onCreate");

        //for accessing in ServiceHandler class
        mContext = this;

        mServer = new ServerUtils(new ServerUtils.MessageCallback() {
            @Override
            public void callbackMessageReceiver(String message) {
                Log.d("Server message: ", message);
            }
        }, null);
    }

    public class SocketBinder extends Binder {
        SocketService getService() {
            return SocketService.this;
        }
    }

    /*@Override
    protected void onHandleIntent(@Nullable Intent intent) {
        if(mServer != null){
            Log.d(TAG, "mserver not null");
        }
        try {
            Log.d("Server: ", "about to begin");
            mServer = new ServerUtils(new ServerUtils.MessageCallback() {
                @Override
                public void callbackMessageReceiver(String message) {
                    Log.d("Server message: ", message);
                }
            }, this, intent.getStringExtra("message"));
        } catch (NullPointerException e) {
            e.printStackTrace();
        }
        mServer.openSocket();
    }*/

    @Override
    public int onStartCommand(Intent intent, int flags, int startId){
        Message message = mServiceHandler.obtainMessage();
        message.arg1 = startId;
        message.obj = intent.getStringExtra("message");
        mServiceHandler.sendMessage(message);

        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent){
        return mBinder;
    }

    @Override
    public void onDestroy(){
        Log.d(TAG, "Destroyed");
    }
}
