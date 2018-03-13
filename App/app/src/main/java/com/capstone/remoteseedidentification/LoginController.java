package com.capstone.remoteseedidentification;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.IBinder;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;

public class LoginController extends AppCompatActivity {
    private final static String TAG = "LoginController";

    SocketService mService;
    boolean mBound = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.INTERNET) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET}, 0);
        }

        bSocketManager = LocalBroadcastManager.getInstance(this);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(BROADCAST_ACTION);
        bSocketManager.registerReceiver(mSocketReceiver, intentFilter);

        Intent intent = new Intent(this, SocketService.class);
        intent.putExtra("message", "connect");

        bindService(intent, mConnection, Context.BIND_AUTO_CREATE);
        //startService(intent);

        ActionBar actionBar = getSupportActionBar();
        //action bar transparent
        //actionBar.setBackgroundDrawable(new ColorDrawable(Color.parseColor("#00000000")));
        //unsure what this does
        //actionBar.setStackedBackgroundDrawable(new ColorDrawable(Color.parseColor("#550000ff")));
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

        if(!etUser.getText().toString().equals("") && !etPass.getText().toString().equals("")) {
            message = "b" + etUser.getText() + "@" + etPass.getText();

            findViewById(R.id.pb_login).setVisibility(View.VISIBLE);

            //open socket with server
//            ServerAsyncTask socketTask = new ServerAsyncTask(mCallback);
//            socketTask.execute(message);

            Log.d(TAG, "doLogin");

            Intent intent = new Intent(this, SocketService.class);
            intent.putExtra("message", message);

            startService(intent);
        }else{
            tvError.setText(R.string.login_error_empty);
            tvError.setVisibility(View.VISIBLE);
        }



        if(loginSuccess) {
            //goMain();
        }
    }

    private void goMain(){
        Intent intent = new Intent(this, MainActivity.class);

        startActivity(intent);
    }

    //established connection between SocketService and LoginController
    //called by onBind in SocketService
    private ServiceConnection mConnection = new ServiceConnection() {
        @Override
        public void onServiceConnected(ComponentName name, IBinder service) {
            SocketService.SocketBinder binder = (SocketService.SocketBinder) service;
            mService = binder.getService();
            Log.d("LoginController", "mService bound");
            mBound = true;
        }

        @Override
        public void onServiceDisconnected(ComponentName name) {
            Log.d("LoginController", "mService disconnected");
            mBound = false;
        }
    };

    public final static String BROADCAST_ACTION = "login_receive";
    private LocalBroadcastManager bSocketManager;
    private BroadcastReceiver mSocketReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            findViewById(R.id.pb_login).setVisibility(View.INVISIBLE);
            if(intent.getStringExtra("message").equals("01")){
                goMain();
            }
        }
    };

    public void doRegister(View v){
        Intent intent = new Intent(this, RegisterController.class);
        startActivity(intent);
    }
}
