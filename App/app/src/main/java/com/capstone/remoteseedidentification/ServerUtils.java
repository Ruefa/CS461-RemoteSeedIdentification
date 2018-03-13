package com.capstone.remoteseedidentification;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.util.Log;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.Socket;

import static java.lang.Thread.sleep;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerUtils {

    private static final String SERVER_IP = "192.168.0.144";
    private static final int SERVER_PORT = 5777;
    private static final String TAG = "ServerUtils";

    public static final String SEND_MESSAGE = "socket.service.intent.action.SEND_MESSAGE";

    private PrintWriter mOutBuffer;
    private BufferedReader mInBuffer;

    private MessageCallback mMessageCallback;
    public boolean mRun;

    public String mInitMessage = "Successfully connected";

    private Socket mSocket;

    public ServerUtils(MessageCallback listener, /*Context context,*/ String message){
        //if(context != null) {
            BroadcastReceiver receiver = new MessageReceiver();
            IntentFilter intentFilter = new IntentFilter();
            intentFilter.addAction(SEND_MESSAGE);
            //context.registerReceiver(receiver, intentFilter);
       // }

        if(message != null){
            mInitMessage = message;
        }

        mMessageCallback = listener;
    }

    public void openSocket() {
        String incomingMessage;

        try {
            InetAddress serverAddr = InetAddress.getByName(SERVER_IP);

            mSocket = new Socket(serverAddr, SERVER_PORT);

            try{
                //setup out buffer with socket
                mOutBuffer = new PrintWriter(new BufferedWriter(
                        new OutputStreamWriter(mSocket.getOutputStream())));

                //create BufferedReader from socket input stream
                mInBuffer = new BufferedReader(new InputStreamReader(mSocket.getInputStream()));
                //sendMessage(mInitMessage);

                //loop endlessly waiting for input data
                //stopSocket() sets mRun to false and ends the loop
                /*while(mRun){
                    Log.d(TAG, "waiting for input");
                    incomingMessage = mInBuffer.readLine();
                    if(incomingMessage != null && mMessageCallback != null){
                        mMessageCallback.callbackMessageReceiver(incomingMessage);
                        return; //temporarilly not using a socket server
                    }
                    incomingMessage = null;
                }*/
            } catch (Exception e){
                e.printStackTrace();
            //empty output buffers and close socket
            } /*finally {
                //mOutBuffer.flush();
                //mOutBuffer.close();
                //socket.close();
            }*/
        } catch (Exception e){
            e.printStackTrace();
        }

        mRun = true;
    }

    public void stopSocket(){
        mRun = false;
    }

    public void sendMessage(String message){
        Log.d("Server: ", "starting sendMessage");
        if(mOutBuffer != null && !mOutBuffer.checkError()){
            mOutBuffer.println(message);
            mOutBuffer.flush();
            Log.d("Server: ", "sent message: " + message);
        }else {
            Log.d("Server: ", "mOutBuffer is null");
        }
    }

    public String receiveMessage(){
        String incomingMessage = null;

        try {
            while (true) {
                incomingMessage = mInBuffer.readLine();
                if (incomingMessage != null && mMessageCallback != null) {
                    return incomingMessage;
                }
                incomingMessage = null;
            }
        }catch (IOException e){
            e.printStackTrace();
        }

        return null;
    }

    //interface to handle data received from socket
    public interface MessageCallback {

        public void callbackMessageReceiver(String message);
    }

    public class MessageReceiver extends BroadcastReceiver {

        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(TAG, "receiver activated message");
            //testString = "broadcast test";
        }
    }
}
