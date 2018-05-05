package com.capstone.remoteseedidentification;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.net.SocketPermission;

public class RegisterController extends AppCompatActivity {

    private static final String TAG = "RegisterController";

    private EditText etUser, etPass, etPassConfirm;
    private TextView tvError;
    private ProgressBar pbRegister;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        etUser = findViewById(R.id.et_register_username);
        etPass = findViewById(R.id.et_register_pass);
        etPassConfirm = findViewById(R.id.et_register_pass_confirm);
        tvError = findViewById(R.id.tv_register_error);
        pbRegister = findViewById(R.id.pb_register);

        mBroadcastManager = LocalBroadcastManager.getInstance(this);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(BROADCAST_ACTION);
        mBroadcastManager.registerReceiver(mBroadcastReceiver, intentFilter);
    }

    public void doRegister(View v){
        final String message;

        tvError.setVisibility(View.INVISIBLE);

        if(etPass.getText().toString().equals(etPassConfirm.getText().toString())
                && !etUser.getText().toString().equals("")
                && !etPass.getText().toString().equals("")) {
            message = ServerUtils.registerFormat(etUser.getText().toString(), etPass.getText().toString());

            pbRegister.setVisibility(View.VISIBLE);
            Intent intent = new Intent(this, SocketService.class);
            Bundle bundle = new Bundle();
            bundle.putString(SocketService.SEND_MESSAGE_KEY, message);
            bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
            intent.putExtras(bundle);
            startService(intent);
        }else{
            tvError.setText(R.string.register_error_mismatch);
            tvError.setVisibility(View.VISIBLE);
        }
    }

    private void goMain(){
        startActivity(new Intent(this, LoginController.class));
    }

    public final static String BROADCAST_ACTION = "register_receive";
    private LocalBroadcastManager mBroadcastManager;

    private BroadcastReceiver mBroadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String response = intent.getStringExtra(SocketService.BROADCAST_KEY);

            pbRegister.setVisibility(View.INVISIBLE);

            switch (response){
                case ServerUtils.REGISTER_ACCEPT:
                    goMain();
                    break;
                case SocketService.BROADCAST_FAILURE:
                    tvError.setText(getString(R.string.login_error_server_connection));
                    tvError.setVisibility(View.VISIBLE);
                    break;
                default:
                    tvError.setText(getString(R.string.login_error_unknown));
                    tvError.setVisibility(View.VISIBLE);
            }
        }
    };
}
