package com.capstone.remoteseedidentification;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.util.Log;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

import static java.lang.Thread.sleep;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerUtils {

    private static final String SERVER_IP = "73.11.102.15";
    private static final int SERVER_PORT = 5777;
    private static final String TAG = "ServerUtils";

    private static final String REGISTER_INDICATOR = "a";
    private static final String LOGIN_INDICATOR = "b";
    private static final String ANALYZE_INDICATOR = "c";
    private static final String REPORT_LIST_INDICATOR = "d";
    private static final String REPORT_INDICATOR = "e";
    private static final String LOGOUT_INDICATOR = "z";

    public static final String SEND_MESSAGE = "socket.service.intent.action.SEND_MESSAGE";
    public static final String LOGIN_ACCEPT = "01";
    public static final String FAILURE = "00";
    public static final String REGISTER_ACCEPT = "01";

    private PrintWriter mOutBuffer;
    private OutputStream mOutputStream;
    private BufferedReader mInBuffer;
    private InputStream mInputStream;
    private Socket mSocket;

    public boolean mRun;

    public String mInitMessage = "Successfully connected";

    private byte[] cookie;

    public ServerUtils(String message){
        BroadcastReceiver receiver = new MessageReceiver();
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(SEND_MESSAGE);


        if(message != null){
            mInitMessage = message;
        }
    }

    public boolean openSocket() {
        String incomingMessage;

        try {
            InetAddress serverAddr = InetAddress.getByName(SERVER_IP);

            //mSocket = new Socket(serverAddr, SERVER_PORT);
            mSocket = new Socket();
            mSocket.connect(new InetSocketAddress(SERVER_IP, SERVER_PORT), 10000);
            mSocket.setKeepAlive(true);
            //mSocket.setSoTimeout(5000); //5 second timeout

            Log.d(TAG, "socket open");

            try{
                //setup out buffer with socket
                mOutBuffer = new PrintWriter(new BufferedWriter(
                        new OutputStreamWriter(mSocket.getOutputStream())));
                mOutputStream = mSocket.getOutputStream();

                //create BufferedReader from socket input stream
                mInBuffer = new BufferedReader(new InputStreamReader(mSocket.getInputStream()));
                mInputStream = mSocket.getInputStream();
                //sendMessage(mInitMessage);

                //loop endlessly waiting for input data
                //stopSocket() sets mRun to false and ends the loop
                /*while(mRun){
                    Log.d(TAG, "waiting for input");
                    incomingMessage = mInBuffer.readLine();
                    if(incomingMessage != null && mMessageCallback != null){
                        return; //temporarilly not using a socket server
                    }
                    incomingMessage = null;
                }*/
            } catch (Exception e){
                e.printStackTrace();
                return false;
            //empty output buffers and close socket
            } /*finally {
                //mOutBuffer.flush();
                //mOutBuffer.close();
                //socket.close();
            }*/
        } catch (Exception e){
            e.printStackTrace();
            return false;
        }

        mRun = true;
        return true;
    }

    public void stopSocket(){
        mRun = false;
        try {
            mSocket.close();
        } catch (IOException e){
            e.printStackTrace();
        }
    }

    public void sendMessage(byte[] message){
        Log.d("Server: ", "starting sendMessage");
        if(mOutBuffer != null && !mOutBuffer.checkError()){
//            mOutBuffer.println(message);
//            mOutBuffer.flush();
            try {
                mOutputStream.write(message);
                mOutputStream.flush();
            }
            catch (IOException e){
                e.printStackTrace();
            }
            Log.d("Server: ", "sent message: " + Arrays.toString(message));
            Log.d("Server: ", "curr cookie: " + Arrays.toString(cookie));
        }else {
            Log.d("Server: ", "mOutBuffer is null");
        }
    }

    public String receiveMessage(String messageType) {
        String incomingMessage = null;
        int available = 0;
        int numBytesRead = 0;
        byte[] bytesRead = new byte[1];

        try {
            //wait for server
            while (available == 0){
                available = mInputStream.available();
            }
//                incomingMessage = mInBuffer.readLine();
//                if (incomingMessage != null) {
//                    Log.d(TAG, incomingMessage);
//                    return incomingMessage;
//                }
//                incomingMessage = null;
//            mInputStream.available();
//            byteRead = mInputStream.read();
//            Log.d(TAG, String.valueOf(byteRead));
//            if(byteRead != -1){
//                byteArrayOutputStream.write(byteRead);

            bytesRead = new byte[available];
            numBytesRead = mInputStream.read(bytesRead);
            Log.d(TAG, Arrays.toString(bytesRead));
        }catch (IOException e){
            e.printStackTrace();
        }

        if(messageType.equals(LoginController.BROADCAST_ACTION)) {
            if (numBytesRead > 1) {
                cookie = bytesRead;
                return LOGIN_ACCEPT;
            } else {
                return FAILURE;
            }
        } else if(messageType.equals(RegisterController.BROADCAST_ACTION)) {
            if (String.valueOf(bytesRead[0]).equals("1")) {
                return LOGIN_ACCEPT;
            } else {
                return FAILURE;
            }
        } else if(messageType.equals(ResultsController.ACTION_VIEW_RESULTS)) {
            return new String(bytesRead, Charset.forName("UTF-8"));
        } else if(messageType.equals(ResultsController.ACTION_REQUEST_RESULT)){
            return new String(bytesRead, Charset.forName("UTF-8"));
        }

        return FAILURE;
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

    public static byte[] stringToByte(String message){
        byte[] messageBytes = message.getBytes(Charset.forName("US-ASCII"));

        ByteBuffer byteBuffer = ByteBuffer.allocate(4);
        byteBuffer.putInt(messageBytes.length);

        byte[] sizeBytes = byteBuffer.array();

        byte[] finalBytes;
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        try {
            outputStream.write(sizeBytes);
            outputStream.write(messageBytes);
        }catch (IOException e){
            e.printStackTrace();
        }

        finalBytes = outputStream.toByteArray();

        Log.d(TAG, String.valueOf(messageBytes.length));
        Log.d(TAG, Arrays.toString(sizeBytes));
        Log.d(TAG, Arrays.toString(finalBytes));

        return finalBytes;
    }

    private static byte[] addLengthToBytes(byte[] bytes){
        ByteBuffer byteBuffer = ByteBuffer.allocate(4);
        byteBuffer.putInt(bytes.length);
        byte[] size = byteBuffer.array();

        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        try {
            byteArrayOutputStream.write(size);
            byteArrayOutputStream.write(bytes);
            return byteArrayOutputStream.toByteArray();
        } catch (IOException e){
            e.printStackTrace();
        }

        return null;
    }

    public byte[] getCookie(){
        return cookie;
    }

    public void removeCookie(){
        cookie = null;
    }

    public static String loginFormat(String username, String pass){
        return LOGIN_INDICATOR + username + "@" + pass;
    }

    public static String registerFormat(String username, String pass){
        return REGISTER_INDICATOR + username + "@" + pass;
    }

    public static byte[] formatResultsList(byte[] userID){
        Log.d(TAG, new String(userID, Charset.forName("UTF-8")));
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        try {
            byteArrayOutputStream.write(REPORT_LIST_INDICATOR.getBytes());
            byteArrayOutputStream.write(userID);
            return addLengthToBytes(byteArrayOutputStream.toByteArray());
        } catch (IOException e){
            e.printStackTrace();
        }
        return null;
    }

    public static byte[] prepareImage(byte[] image, byte[] userID){
        byte[] finalBytes = new byte[1];
        byte[] preLength;

        ByteArrayOutputStream combiner = new ByteArrayOutputStream();
        try {
            combiner.write(ANALYZE_INDICATOR.getBytes());
            combiner.write(userID);
            combiner.write("|".getBytes());
            combiner.write(image);
            preLength = combiner.toByteArray();

            ByteBuffer byteBuffer = ByteBuffer.allocate(4);
            byteBuffer.putInt(preLength.length);

            byte[] sizeBytes = byteBuffer.array();
            combiner.reset();
            combiner.write(sizeBytes);
            combiner.write(preLength);
            finalBytes = combiner.toByteArray();
        } catch (IOException e){
            e.printStackTrace();
        }

        return finalBytes;
    }

    public static byte[] formatResultRequest(byte[] reportID, byte[] userID){
        try{
            ByteArrayOutputStream combiner = new ByteArrayOutputStream();
            combiner.write(REPORT_INDICATOR.getBytes());
            combiner.write(userID);
            combiner.write("|".getBytes());
            combiner.write(reportID);
            return addLengthToBytes(combiner.toByteArray());
        } catch (IOException e){
            e.printStackTrace();
        }

        return null;
    }
}
