package water.api;

import water.Key;

import com.google.gson.JsonObject;

public class Cancel extends Request {
  protected final Str _key = new Str(KEY);

  @Override
  protected Response serve() {
    String key = _key.value();

    try {
      water.Jobs.cancel(Key.make(key));
    } catch( Exception e ) {
      return Response.error(e.getMessage());
    }

    JsonObject response = new JsonObject();
    return Response.redirect(response, Jobs.class, null);
  }
}