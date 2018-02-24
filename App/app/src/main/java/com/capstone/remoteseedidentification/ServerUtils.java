package com.capstone.remoteseedidentification;

import android.util.Log;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.Socket;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerUtils {

    private static final String SERVER_IP = "192.168.0.144";
    private static final int SERVER_PORT = 5777;

    private PrintWriter mOutBuffer;
    private BufferedReader mInBuffer;

    private MessageCallback mMessageCallback;
    private boolean mRun;

    public ServerUtils(MessageCallback listener){
        mMessageCallback = listener;
    }

    public void openSocket() {
        String incomingMessage;

        mRun = true;

        try {
            InetAddress serverAddr = InetAddress.getByName(SERVER_IP);

            Socket socket = new Socket(serverAddr, SERVER_PORT);

            try{
                //setup out buffer with socket
                mOutBuffer = new PrintWriter(new BufferedWriter(
                        new OutputStreamWriter(socket.getOutputStream())));

                //create BufferedReader from socket input stream
                mInBuffer = new BufferedReader(new InputStreamReader(socket.getInputStream()));

                //loop endlessly waiting for input data
                //stopSocket() sets mRun to false and ends the loop
                while(mRun){
                    incomingMessage = mInBuffer.readLine();
                    if(incomingMessage != null && mMessageCallback != null){
                        mMessageCallback.callbackMessageReceiver(incomingMessage);
                    }
                    incomingMessage = null;
                }
            } catch (Exception e){
                e.printStackTrace();
            //empty output buffers and close socket
            } finally {
                mOutBuffer.flush();
                mOutBuffer.close();
                socket.close();
            }
        } catch (Exception e){
            e.printStackTrace();
        }
    }

    public void stopSocket(){
        mRun = false;
    }

    public void sendMessage(String message){
        Log.d("Server: ", "starting sendMessage");
        if(mOutBuffer != null && !mOutBuffer.checkError()){
            mOutBuffer.println(message);
            mOutBuffer.flush();
            Log.d("Server: ", "sent message" + message);
        }else {
            Log.d("Server: ", "mOutBuffer is null");
        }
    }

    //interface to handle data received from socket
    public interface MessageCallback {

        public void callbackMessageReceiver(String message);
    }
}
