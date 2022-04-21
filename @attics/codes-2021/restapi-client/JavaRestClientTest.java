import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Map;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * Usage:
 *
 * Download this file and unzip it on a lib folder (If it is on another folder, make sure to change it on the commands)
 * Compile this file with this command
 * javac -cp lib/json-simple-1.1.1.jar JavaRestClientTest.java
 * Run the class with the command
 * java -cp lib/json-simple-1.1.1.jar:./ JavaRestClientTest
 */
public class JavaRestClientTest {

	public static String POST(URL url, JSONObject data) {
		String rtn = "";

		try {
			
            HttpURLConnection httpConnection  = (HttpURLConnection) url.openConnection();
            httpConnection.setDoOutput(true);
            httpConnection.setRequestMethod("POST");
            httpConnection.setRequestProperty("Content-Type", "application/json");
            httpConnection.setRequestProperty("Accept", "application/json");

            DataOutputStream wr = new DataOutputStream(httpConnection.getOutputStream());
            wr.write(data.toString().getBytes());
            Integer responseCode = httpConnection.getResponseCode();

            BufferedReader bufferedReader;

            if (responseCode > 199 && responseCode < 300) {
                bufferedReader = new BufferedReader(new InputStreamReader(httpConnection.getInputStream()));
            } else {
                bufferedReader = new BufferedReader(new InputStreamReader(httpConnection.getErrorStream()));
            }

            StringBuilder content = new StringBuilder();
            String line;
            while ((line = bufferedReader.readLine()) != null) {
                content.append(line).append("\n");
            }
            bufferedReader.close();

            //System.out.println(content.toString());
            
            rtn = content.toString();
			
		} catch (Exception e){
			System.err.println("ERROR : " + e.toString());
			rtn = e.toString();
		}
		
		return rtn;
		
	}

    public static void main(String[] args) {

        try {        	

            String sql_string = "";
            //sql_string = "create model mdl(pm25 real, pres real) from pm25.csv method uniform size 1000";
    		//sql_string = "select model count (pm25 real) from mdl where 1000 <= pres <= 1020";
    		//sql_string = "select model sum (pm25 real) from mdl where 1000 <= pres <= 1020";
    		//sql_string = "select model avg (pm25 real) from mdl where 1000 <= pres <= 1020";

    		sql_string = "create model instacart_order_product_600k (add_to_cart_order real, reordered real) from instacart_order_product_600k.csv method uniform size 1000";
    		//sql_string = "select model count (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0";
    		//sql_string = "select model sum (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0";
    		//sql_string = "select model avg (add_to_cart_order real) from instacart_order_product_600k where 0.9 <= reordered <= 1.0";
    		//sql_string = "show model ";
    		//sql_string = "drop model instacart_order_product_600k";
    		
            JSONObject data = new JSONObject();
            data.put("sql_string", sql_string);

            URL url = new URL("http://127.0.0.1:1234");
            File f = new File("./url.txt");
            if (f.exists())
            {
               String url_str = Files.readString(Paths.get("./url.txt"));
               url = new URL(url_str);
            }            
            System.out.println(url);         

            
            String rtn = POST(url, data);
            
            System.out.println(rtn.toString());         

        } catch (Exception e) {
            System.out.println("Error Message");
            System.out.println(e.getClass().getSimpleName());
            System.out.println(e.getMessage());
        }
    }

}