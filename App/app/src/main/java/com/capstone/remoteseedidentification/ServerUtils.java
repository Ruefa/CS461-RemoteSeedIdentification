package com.capstone.remoteseedidentification;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.SystemClock;
import android.util.Log;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.ByteArrayInputStream;
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
import java.util.LinkedList;
import java.util.List;

import static java.lang.Thread.sleep;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerUtils {

    private static final String SERVER_IP = "73.11.102.15";
    private static final int SERVER_PORT = 5777;
    private static final String TAG = "ServerUtils";

    private static final byte REGISTER_INDICATOR = 0x01;
    private static final byte LOGIN_INDICATOR = 0x02;
    private static final byte ANALYZE_INDICATOR = 0x64;
    private static final byte REPORT_LIST_INDICATOR = 0x65;
    private static final byte REPORT_INDICATOR = 0x66;
    private static final byte LOGOUT_INDICATOR = 0x63;
    private static final byte FORGOTPW_INDICATOR = 0x05;
    private static final byte CHANGEPW_INDICATOR = 0x04;
    private static final byte DELETE_RESULT_INDICATOR = 0x67;

    public static final String SEND_MESSAGE = "socket.service.intent.action.SEND_MESSAGE";
    public static final String SUCCESS_STRING = "00";
    public static final String LOGIN_ACCEPT = "01";
    public static final String FORGOT_ACCEPT = "10";
    public static final String CHANGE_ACCEPT = "10";
    public static final String FAILURE = "02";
    public static final String REGISTER_ACCEPT = "00";
    public static final String DUP_USER_STRING = "0A";
    public static final String BAD_CRED = "0C";
    public static final String REPORT_NOT_FINISHED_STRING = "14";

    public static final byte SUCCESS = 0x00;
    public static final byte INVALID_MESSAGE = 0x32;
    public static final byte FAILURE_BYTES = 0x01;
    public static final byte DUP_USER = 0x0A;
    public static final byte INVALID_CRED = 0x0C;
    public static final byte REPORT_NOT_READY  = 0x14;

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

            } catch (Exception e){
                e.printStackTrace();
                return false;
            //empty output buffers and close socket
            }
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
        ByteArrayOutputStream combiner = new ByteArrayOutputStream();

        try {
            // get number of bytes being sent across socket
            byte[] sizeBytes = new byte[4];
            mInputStream.read(sizeBytes);
            Log.d(TAG, "byte size: " + Arrays.toString(sizeBytes));

            int messageSize = ByteBuffer.wrap(sizeBytes).getInt();
            // largest # of bytes to read from socket at a time
            int maxBlockSize = 16384; // 2^14

            do {
                byte[] bytesToCombine;
                bytesToCombine = messageSize >= maxBlockSize ? new byte[maxBlockSize] : new byte[messageSize];
                numBytesRead = mInputStream.read(bytesToCombine);

                messageSize -= numBytesRead;

                if(numBytesRead > 0) {
                    combiner.write(bytesToCombine, 0, numBytesRead);
                }
            }while(messageSize > 0);

            bytesRead = combiner.toByteArray();
            Log.d(TAG, Arrays.toString(bytesRead));
        }catch (IOException e){
            e.printStackTrace();
        }

        // login
        if(messageType.equals(LoginController.BROADCAST_ACTION)) {
            Log.d(TAG, String.valueOf(bytesRead[0]));
            if (bytesRead[0] == SUCCESS) {
                cookie = bytesRead;
                return LOGIN_ACCEPT;
            } else if(bytesRead[0] == INVALID_CRED) {
                return BAD_CRED;
            } else {
                return FAILURE;
            }

          // forgot password
        } else if(messageType.equals(LoginController.BROADCAST_ACTION_FORGOT)) {
            if(bytesRead[0] == SUCCESS) {
                return FORGOT_ACCEPT;
            } else{
                return FAILURE;
            }

          // register
        } else if(messageType.equals(RegisterController.BROADCAST_ACTION)) {
            if (bytesRead[bytesRead.length-1] == SUCCESS) {
                return REGISTER_ACCEPT;
            } else if(bytesRead[bytesRead.length-1] == DUP_USER) {
                return DUP_USER_STRING;
            } else {
                return FAILURE;
            }
          // main activity
        } else if(messageType.equals(MainActivity.BROADCAST_ACTION)) {
            if(bytesRead[0] == SUCCESS){
                if(bytesRead.length > 1) {
                    return SUCCESS_STRING;
                } else {
                    return CHANGE_ACCEPT;
                }
            } else if(bytesRead[0] == INVALID_CRED) {
                return BAD_CRED;
            } else {
                return FAILURE;
            }

        } else if(messageType.equals(ResultsController.ACTION_VIEW_RESULTS)) {
            return new String(bytesRead, Charset.forName("ASCII"));

        } else if(messageType.equals(ResultsController.ACTION_REQUEST_RESULT)){
            if(bytesRead[0] == INVALID_MESSAGE){
                return FAILURE;
            } else if(bytesRead[0] == REPORT_NOT_READY) {
                return REPORT_NOT_FINISHED_STRING;
            } else {
                //find location of delimiter
                List<byte[]> byteList = new LinkedList<>();
                int i = 0;
                int block = 0;
                int found = 0;
                while (i < bytesRead.length) {
                    if(bytesRead[i] == "|".getBytes()[0] && found < 2){
                        byteList.add(Arrays.copyOfRange(bytesRead, block, i));
                        block = i + 1;
                        found++;
                    }
                    i++;
                }
                // get last item
                byteList.add(Arrays.copyOfRange(bytesRead, block, bytesRead.length));

                byte[] data = byteList.get(1);
                byte[] imageBytes = byteList.get(2);

                Log.d(TAG, Arrays.toString(data));
                String resultString = "";
                for (int j = 0; j < data.length; j++) {
                    resultString += new String(new byte[]{data[j]}, Charset.forName("ASCII"));
                }
                Log.d(TAG, Arrays.toString(imageBytes));

                String fileName = MainActivity.imageToFile("result.png", imageBytes);

                return resultString + "\n" + fileName;
            }
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

    // converts a single byte to a ISO_8859_1 string
    // used for indicators so they are converted back to bytes correctly before sending
    private static String byteToISOString(byte indicatorByte){
        byte[] bytes = new byte[]{indicatorByte};
        String indicator = "";

        try {
            indicator = new String(bytes, "ISO_8859_1");
        } catch (Exception e){
            e.printStackTrace();
        }

        return indicator;
    }

    public static String loginFormat(String username, String pass){
        return byteToISOString(LOGIN_INDICATOR) + username + ":" + pass;
    }

    public static String registerFormat(String username, String pass){
        return byteToISOString(REGISTER_INDICATOR) + username + ":" + pass;
    }

    public static String forgotPWFormat(String username){
        return byteToISOString(FORGOTPW_INDICATOR) + username;
    }

    public static String changePWFormat(String oldPW, String newPW){
        return byteToISOString(CHANGEPW_INDICATOR) + oldPW + "|" + newPW;
    }

    public static byte[] formatResultsList(byte[] userID){
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        try {
            byteArrayOutputStream.write(REPORT_LIST_INDICATOR);
            //byteArrayOutputStream.write(userID);
            return addLengthToBytes(byteArrayOutputStream.toByteArray());
        } catch (Exception e){
            e.printStackTrace();
        }
        return null;
    }

    public static String deleteResultFormat(String resultID){
        return byteToISOString(DELETE_RESULT_INDICATOR) + resultID;
    }

    public static byte[] prepareImage(byte[] image, byte[] userID){
        byte[] finalBytes = new byte[1];
        byte[] preLength;

        ByteArrayOutputStream combiner = new ByteArrayOutputStream();
        try {
            combiner.write(ANALYZE_INDICATOR);
            //combiner.write(userID);
            //combiner.write("|".getBytes());
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
            combiner.write(REPORT_INDICATOR);
            //combiner.write(userID);
            //combiner.write("|".getBytes());
            combiner.write(reportID);
            return addLengthToBytes(combiner.toByteArray());
        } catch (IOException e){
            e.printStackTrace();
        }

        return null;
    }
}
