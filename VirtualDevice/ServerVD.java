import java.io.*;
import java.util.*;
import java.net.*;
public class ServerVD implements Runnable {
	Socket client;
	HashMap<String, String> request;
	BufferedReader dataIn;
	private PrintStream dataOut;
	public static void main(String... a) throws IOException  {
		System.out.println("\n\tjavac ServerVD.java && java ServerVD <port>\n\t\t\thttp://localhost:"+((a.length>0)?Integer.parseInt(a[0]):1850));
		while (true)(new Thread(new ServerVD((new ServerSocket((a.length>0)?Integer.parseInt(a[0]):1850)).accept()))).start(); 
	}
	ServerVD(Socket s) throws IOException {
		this.client = s;
		this.request = new HashMap<String, String>();
		this.dataIn = new BufferedReader(new InputStreamReader(this.client.getInputStream()));
		this.dataOut = new PrintStream(this.client.getOutputStream());
	}
	public void run() {
		String data = "";
		String[] line;
		try { while(!(line=this.dataIn.readLine().split(":",2))[0].equals(""))if(line.length>1)this.request.put(line[0].trim(),line[1].trim());} 
		catch (Exception e){ System.out.println("ERROR!"); }
		try {
			InputStream input = ServerVD.class.getResourceAsStream("./protocol.raw");
			BufferedReader br = new BufferedReader(new InputStreamReader(input));
			data = data + "HTTP/1.1 200 OK\r\n";
			data = data + "Server: CC8 IoT DEMO\r\n";
			data = data + "Content-Length: " + input.available() + "\r\n";
			data = data + "Access-Control-Allow-Origin: " + this.request.get("Origin") + "\r\n";
			data = data + "Content-Type: text/plain\r\n";
			data = data + "\r\n";
			data = data + br.readLine();
		} catch (Exception e) {
			data = data + "HTTP/1.1 404 Not Found\r\n";
			data = data + "Server: CC8 IoT\r\n";
			data = data + "Content-Length: 24\r\n";
			data = data + "Access-Control-Allow-Origin: " + this.request.get("Origin") + "\r\n";
			data = data + "Content-Type: text/plain\r\n";
			data = data + "\r\n";
			data = data + "00F000000000000000000000";
		}
		this.dataOut.print(data);
		try { this.dataOut.close(); this.client.close();} 
		catch (Exception e) { System.out.println("Error Close Client"); } 
	}
}