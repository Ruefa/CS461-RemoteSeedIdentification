import android.util.Log;

import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.Socket;

/**
 * Created by Alex on 2/22/2018.
 */

public class ServerUtils {

    private static final String SERVER_IP = "";
    private static final int SERVER_PORT = 5777;

    private PrintWriter mOutBuffer;
    private MessageCallback mMessageCallback;

    public ServerUtils(MessageCallback listener){
        mMessageCallback = listener;
    }

    public void openSocket() {

        try {
            InetAddress serverAddr = InetAddress.getByName(SERVER_IP);

            Socket socket = new Socket(serverAddr, SERVER_PORT);
        } catch (Exception e){
            e.printStackTrace();
        }
    }

    public interface MessageCallback {

        public void callbackMessageReceiver(String message);
    }
}
