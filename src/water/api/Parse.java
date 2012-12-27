
package water.api;

import com.google.gson.JsonObject;
import water.Key;
import water.Value;
import water.parser.ParseDataset;

public class Parse extends Request {
  protected final H2OExistingKey _source = new H2OExistingKey(RequestStatics.SOURCE_KEY);
  protected final H2OKey _dest = new H2OKey(RequestStatics.DEST_KEY, (Key)null);

  @Override protected Response serve() {
    Value source = _source.value();
    Key dest = _dest.value();
    if (dest == null) {
      String n = source._key.toString();
      int dot = n.lastIndexOf('.');
      if( dot > 0 ) n = n.substring(0, dot);
      dest = Key.make(n+".hex");
    }
    try {
      ParseDataset.parse(dest, source);
      JsonObject response = new JsonObject();
      response.addProperty(RequestStatics.DEST_KEY,dest.toString());
      Response r = Response.done(response);
      r.setBuilder(RequestStatics.DEST_KEY, new KeyElementBuilder());
      return r;
    } catch (IllegalArgumentException e) {
      return Response.error(e.getMessage());
    } catch (Error e) {
      return Response.error(e.getMessage());
    }
  }

}
