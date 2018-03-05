package com.capstone.remoteseedidentification;

import android.Manifest;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.IBinder;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;

public class LoginController extends AppCompatActivity {

    SocketService mService;
    boolean mBound = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.INTERNET) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET}, 0);
        }
    }

    public void doLogin(View v){
        boolean loginSuccess = true;
        EditText etUser, etPass;
        TextView tvError;
        final String message;

        etUser = findViewById(R.id.edit_username);
        etPass = findViewById(R.id.edit_pass);
        tvError = findViewById(R.id.tv_login_error);

        tvError.setVisibility(View.INVISIBLE);

        //Log.d("errorTest", )
        if(!etUser.getText().toString().equals("Username") && !etPass.toString().equals("Password")) {
            message = "b" + etUser.getText() + "@" + etPass.getText();

            findViewById(R.id.pb_login).setVisibility(View.VISIBLE);

            //open socket with server
            ServerAsyncTask socketTask = new ServerAsyncTask(mCallback);
            socketTask.execute(message);
        }else{
            tvError.setText(R.string.login_error_empty);
            tvError.setVisibility(View.VISIBLE);
        }

        /*Intent intent = new Intent(this, SocketService.class);
        startService(intent);*/

        /*bindService(intent, mConnection, Context.BIND_AUTO_CREATE);
        if (!mBound) {
            Log.d("LoginController", "mService null");
        }else{
            Log.d("LoginController", "mService not null");
        }*/

        if(loginSuccess) {
            //goMain();
        }
    }

    public void broadCastTest(View v){
        Intent broadCastIntent = new Intent();
        broadCastIntent.setAction(ServerUtils.SEND_MESSAGE);
        sendBroadcast(broadCastIntent);
    }

    private void goMain(){
        Intent intent = new Intent(this, MainActivity.class);

        startActivity(intent);
    }

    //maybe move?
    private ServiceConnection mConnection = new ServiceConnection() {
        @Override
        public void onServiceConnected(ComponentName name, IBinder service) {
            SocketService.SocketBinder binder = (SocketService.SocketBinder) service;
            mService = binder.getService();
            //mBinder = binder;
            Log.d("LoginController", "mService bound");
            //mService.openSocket();
            mBound = true;
            try {Thread.sleep(3000);} catch (InterruptedException e){}
            
        }

        @Override
        public void onServiceDisconnected(ComponentName name) {
            Log.d("LoginController", "mService disconnected");
        }
    };

    private ServerUtils.MessageCallback mCallback = new ServerUtils.MessageCallback() {
        @Override
        public void callbackMessageReceiver(String message) {
            Log.d("Server message: ", message);

            if(message.equals("01")){
                goMain();
            }else{
                findViewById(R.id.pb_login).setVisibility(View.INVISIBLE);
            }
        }
    };

    public void doRegister(View v){

    }
}
