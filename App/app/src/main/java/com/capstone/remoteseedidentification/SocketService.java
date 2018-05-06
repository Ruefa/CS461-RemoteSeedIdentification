package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.os.Binder;
import android.os.Bundle;
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

    public final static String BROADCAST_KEY = "message";
    public final static String BROADCAST_FAILURE = "failure";

    public final static String SEND_MESSAGE_KEY = "message";
    public final static String OUTBOUND_KEY = "outbound";
    public final static String SEND_IMAGE_KEY = "image";
    public final static String ACTION_KEY = "action";

    public final static String RESET = "_reset";

    private final class ServiceHandler extends Handler {
        public ServiceHandler(Looper looper){
            super(looper);
        }

        public void handleMessage(Message message){
            boolean socketSuccess = false;
            byte[] messageToSend;

            Log.d(TAG, "handling message");

            mServer.mInitMessage = (String) message.obj;
            if(!mServer.mRun) {
                Log.d(TAG, "open socket");
                socketSuccess =  mServer.openSocket();
            }

            Intent intent = new Intent(message.getData().getString(OUTBOUND_KEY));
            if(socketSuccess || mServer.mRun) {
                if(message.getData().getString(ACTION_KEY) != null){
                    // request result detail
                    if(message.getData().getString(ACTION_KEY).equals(ResultsController.ACTION_REQUEST_RESULT)){
                        Log.d(TAG, "request result");
                        intent.putExtra(ACTION_KEY, message.getData().getString(ACTION_KEY));
                        try {
                            mServer.sendMessage(ServerUtils.formatResultRequest(
                                    message.getData().getString(SEND_MESSAGE_KEY).getBytes("ASCII"), //change
                                    mServer.getCookie()
                            ));
                        } catch (Exception e){
                            e.printStackTrace();
                        }
                    } else if(message.getData().getString(ACTION_KEY).equals(ResultsController.ACTION_VIEW_RESULTS)) {
                        Log.d(TAG, "results list request");
                        intent.putExtra(ACTION_KEY, message.getData().getString(ACTION_KEY));
                        messageToSend = ServerUtils.formatResultsList(mServer.getCookie());
                        mServer.sendMessage(messageToSend);
                    }
                }else {
                    if (message.getData().getString(SEND_IMAGE_KEY) != null) {
                        Log.d(TAG, "sending image");
                        mServer.sendMessage(ServerUtils.prepareImage(
                                MainActivity.fileToBytes(message.getData().getString(SEND_IMAGE_KEY)),
                                mServer.getCookie()
                        ));
                    } else {
                        messageToSend = ServerUtils.stringToByte(message.getData().getString(SEND_MESSAGE_KEY));
                        mServer.sendMessage(messageToSend);
                    }
                }

                String incomingMessage;
                Log.d(TAG, "waiting to receive message");
                if(message.getData().getString(ACTION_KEY) != null){
                    incomingMessage = mServer.receiveMessage(message.getData().getString(ACTION_KEY));
                }else {
                    incomingMessage = mServer.receiveMessage(message.getData().getString(OUTBOUND_KEY));
                }
                Log.d(TAG, "received message");
                //mServer.stopSocket();

                intent.putExtra(BROADCAST_KEY, incomingMessage);
            }else{
                intent.putExtra(BROADCAST_KEY, BROADCAST_FAILURE);
            }
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

        mServer = new ServerUtils(null);
    }

    public class SocketBinder extends Binder {
        SocketService getService() {
            return SocketService.this;
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId){
        Log.d(TAG, "command received");
        Message message = mServiceHandler.obtainMessage();
        message.arg1 = startId;
        if(intent.getStringExtra(SEND_MESSAGE_KEY).equals(RESET)){
            mServer.removeCookie();
            try {
                mServer.stopSocket();
            } catch (Exception e){
                e.printStackTrace();
            }
        } else {
            message.setData(intent.getExtras());
            mServiceHandler.sendMessage(message);
        }

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
