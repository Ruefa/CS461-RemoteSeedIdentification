package com.capstone.remoteseedidentification;

import android.os.AsyncTask;
import android.util.Log;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerAsyncTask extends AsyncTask<String, String, ServerUtils> {

    private ServerUtils mServer;

    //constructor currently takes no args
    //public ServerAsyncTask(){}

    @Override
    protected ServerUtils doInBackground(String... strings) {

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
        return null;
    }
}
