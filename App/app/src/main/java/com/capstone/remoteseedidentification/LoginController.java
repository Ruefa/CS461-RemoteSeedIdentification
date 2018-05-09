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
import android.widget.Switch;
import android.widget.TextView;

public class LoginController extends AppCompatActivity {
    private final static String TAG = "LoginController";

    SocketService mService;
    boolean mBound = false;

    private TextView mTVError;

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

        mTVError = findViewById(R.id.tv_login_error);
    }

    public void doLogin(View v){
        EditText etUser, etPass;
        final String message;

        // get edit text components from layout
        etUser = findViewById(R.id.edit_username);
        etPass = findViewById(R.id.edit_pass);

        mTVError.setVisibility(View.INVISIBLE);

        // user input validation
        if(!etUser.getText().toString().equals("") && !etPass.getText().toString().equals("")) {

            findViewById(R.id.pb_login).setVisibility(View.VISIBLE);

            message = ServerUtils.loginFormat(etUser.getText().toString(), etPass.getText().toString());

            Log.d(TAG, "doLogin");

            Intent intent = new Intent(this, SocketService.class);
            Bundle bundle = new Bundle();
            bundle.putString(SocketService.SEND_MESSAGE_KEY, message);
            bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
            intent.putExtras(bundle);

            startService(intent);
        }else{
            mTVError.setText(R.string.login_error_empty);
            mTVError.setVisibility(View.VISIBLE);
        }
    }

    private void goMain(){
        Intent intent = new Intent(this, MainActivity.class);

        startActivity(intent);
    }

    //established connection between SocketService and LoginController
    //binding keeps service alive which keeps the socket alive
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
            String response = intent.getStringExtra(SocketService.BROADCAST_KEY);
            switch(response){
                case ServerUtils.LOGIN_ACCEPT:
                    goMain();
                    break;
                case SocketService.BROADCAST_FAILURE:
                    mTVError.setText(getText(R.string.login_error_server_connection));
                    mTVError.setVisibility(View.VISIBLE);
                    break;
                default:
                    mTVError.setText(getString(R.string.login_error_unknown));
                    mTVError.setVisibility(View.VISIBLE);
            }
        }
    };

    public void doRegister(View v){
        Intent intent = new Intent(this, RegisterController.class);
        startActivity(intent);
    }

    public void skipLogin(View v){
        Intent intent = new Intent(this, MainActivity.class);
        startActivity(intent);
    }

    public void forgotPassword(View v){
        // todo
    }
}
