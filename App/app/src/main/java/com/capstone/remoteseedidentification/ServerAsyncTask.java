package com.capstone.remoteseedidentification;

import android.os.AsyncTask;
import android.util.Log;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerAsyncTask extends AsyncTask<String, String, ServerUtils> {

    private ServerUtils mServer;
    private ServerUtils.MessageCallback mCallback;

    //constructor currently takes no args
    public ServerAsyncTask(ServerUtils.MessageCallback callback){
        super();

        mCallback = callback;
    }

    @Override
    protected ServerUtils doInBackground(String... strings) {

        try{
            Log.d("Server: ", "about to begin");
            //mServer = new ServerUtils(mCallback, null, strings[0]);
        } catch (NullPointerException e){
            e.printStackTrace();
        }
        mServer.openSocket();
        return null;
    }
}
