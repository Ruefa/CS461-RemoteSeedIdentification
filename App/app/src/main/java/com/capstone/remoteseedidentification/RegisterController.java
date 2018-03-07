package com.capstone.remoteseedidentification;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;

public class RegisterController extends AppCompatActivity {

    private static final String TAG = "RegisterController";

    private EditText etUser, etPass, etPassConfirm;
    private TextView tvError;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        etUser = findViewById(R.id.et_register_username);
        etPass = findViewById(R.id.et_register_pass);
        etPassConfirm = findViewById(R.id.et_register_pass_confirm);
        tvError = findViewById(R.id.tv_register_error);
    }

    public void doRegister(View v){
        final String message;

        tvError.setVisibility(View.INVISIBLE);

        if(etPass.getText().toString().equals(etPassConfirm.getText().toString())) {
            message = "a" + etUser.getText().toString() + "@" + etPass.getText().toString();

            ServerAsyncTask asyncTask = new ServerAsyncTask(mCallback);
            asyncTask.execute(message);
        }else{
            tvError.setText(R.string.register_error_mismatch);
            tvError.setVisibility(View.VISIBLE);
        }
    }

    private ServerUtils.MessageCallback mCallback = new ServerUtils.MessageCallback() {
        @Override
        public void callbackMessageReceiver(String message) {
            Log.d(TAG, message);
        }
    };
}
