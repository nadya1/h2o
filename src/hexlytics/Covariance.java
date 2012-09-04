package hexlytics;
import java.io.*;

import com.sun.org.apache.xml.internal.serialize.Serializer;

import water.*;
import water.serialization.RTSerializer;
import water.serialization.RemoteTaskSerializer;

/**
 * Calculate the covariance and correlation of two variables
 * 
 * @author alex@0xdata.com
 */
public abstract class Covariance {

  static public String run( ValueArray ary, int colA, int colB ) {
    StringBuilder sb = new StringBuilder();
    
    sb.append("Covariance of ").append(ary._key).append(" between ").
      append(colA).append(" and ").append(colB);

    COV_Task cov = new COV_Task();
    cov._arykey = ary._key;
    cov._colA = colA;
    cov._colB = colB;

    // Pass 1: compute sums for averages
    cov._pass = 1;
    long start = System.currentTimeMillis();
    cov.invoke(ary._key);
    long pass1 = System.currentTimeMillis();
    sb.append("<p>Pass 1 in ").append(pass1-start).append("msec");

    // Pass 2: Compute the product of variance for variance and covariance
    long n = ary.num_rows();
    cov._pass = 2;
    cov._Xbar = cov._sumX / n;
    cov._Ybar = cov._sumY / n;
    cov.reinitialize();
    cov.invoke(ary._key);
    long pass2 = System.currentTimeMillis();
    sb.append("<P>Pass 2 in ").append(pass2-pass1).append("msec");


    // Compute results
    // We divide by n-1 since we lost a df by using a sample mean
    double varianceX = cov._XXbar / (n - 1);
    double varianceY = cov._YYbar / (n - 1);
    double sdX = Math.sqrt(varianceX);
    double sdY = Math.sqrt(varianceY);
    double covariance = cov._XYbar / (n - 1);
    double correlation = covariance / sdX / sdY;

    // Print results
    sb.append("<p>Covariance = ").append(covariance);
    sb.append("<p>Correlation = ").append(correlation);

    sb.append("<p><table><tr><td></td><td>Var ").append(colA).append("</td><td>Var ").append(colB).append("</td></tr>");
    sb.append("<tr><td>Mean </td><td>").append(cov._Xbar).append("</td><td>").append(cov._Ybar).append("</td></tr>");
    sb.append("<tr><td>Standard Deviation </td><td>").append(sdX).append("</td><td>").append(sdY).append("</td></tr>");
    sb.append("<tr><td>Variance </td><td>").append(varianceX).append("</td><td>").append(varianceY).append("</td></tr>");
    sb.append("</table>");
    
    return sb.toString();
  }

  @RTSerializer(COV_Task.Serializer.class)
  public static class COV_Task extends MRTask {
    Key _arykey;                // Main ValueArray key
    int _pass;                  // Pass 1, or 2.
    int _colA, _colB;           // Which columns to work on
    double _sumX,_sumY;
    double _Xbar, _Ybar, _XXbar, _YYbar, _XYbar;
    public static class Serializer extends RemoteTaskSerializer<COV_Task> {
      @Override public int wire_len(COV_Task t) { return 4+4+4+12*8+t._arykey.wire_len(); }
      @Override public int write( COV_Task t, byte[] buf, int off ) {
        off += UDP.set4 (buf,off,t._pass);
        off += UDP.set4 (buf,off,t._colA);
        off += UDP.set4 (buf,off,t._colB);
        off += UDP.set8d(buf,off,t._sumX);
        off += UDP.set8d(buf,off,t._sumY);

        off += UDP.set8d(buf,off,t._Xbar);
        off += UDP.set8d(buf,off,t._Ybar);
        off += UDP.set8d(buf,off,t._XXbar);
        off += UDP.set8d(buf,off,t._YYbar);
        off += UDP.set8d(buf,off,t._XYbar);

        off += t._arykey.write(buf,off);
        return off;
      }
      @Override public COV_Task read( byte[] buf, int off ) { 
        COV_Task t = new COV_Task();
        t._pass = UDP.get4 (buf,(off+=4)-4);
        t._colA = UDP.get4 (buf,(off+=4)-4);
        t._colB = UDP.get4 (buf,(off+=4)-4);
        t._sumX = UDP.get8d(buf,(off+=8)-8);
        t._sumY = UDP.get8d(buf,(off+=8)-8);

        t._Xbar = UDP.get8d(buf,(off+=8)-8);
        t._Ybar = UDP.get8d(buf,(off+=8)-8);
        t._XXbar= UDP.get8d(buf,(off+=8)-8);
        t._YYbar= UDP.get8d(buf,(off+=8)-8);
        t._XYbar= UDP.get8d(buf,(off+=8)-8);

        t._arykey  = Key.read(buf,off);
        return t;
      }
      @Override public void write( COV_Task t, DataOutputStream dos ) { throw new Error("do not call"); }
      @Override public COV_Task read ( DataInputStream  dis ) { throw new Error("do not call"); }
    }

    public void map( Key key ) {
      // Get the root ValueArray for the metadata
      ValueArray ary = (ValueArray)DKV.get(_arykey);
      // Get the raw bits to work on
      byte[] bits = DKV.get(key).get();
      // Split out all the loop-invariant meta-data offset into
      int rowsize = ary.row_size();
      int rows = bits.length/rowsize;
      int colA_off  = ary.col_off  (_colA);
      int colB_off  = ary.col_off  (_colB);
      int colA_size = ary.col_size (_colA);
      int colB_size = ary.col_size (_colB);
      int colA_base = ary.col_base (_colA);
      int colB_base = ary.col_base (_colB);
      int colA_scale= ary.col_scale(_colA);
      int colB_scale= ary.col_scale(_colB);
      // Loop over the data
      switch( _pass ) {
      case 1:                   // Pass 1
        // Run pass 1
        // Calculate sums for averages
        for( int i=0; i<rows; i++ ) {
          double X = ary.datad(bits,i,rowsize,colA_off,colA_size,colA_base,colA_scale,_colA);
          double Y = ary.datad(bits,i,rowsize,colB_off,colB_size,colB_base,colB_scale,_colB);
          _sumX += X;
          _sumY += Y;
        }
        break;

      case 2:                   // Pass 2
        // Run pass 2
        // Calculate the product of de-meaned variables
        for( int i=0; i<rows; i++ ) {
          double X = ary.datad(bits,i,rowsize,colA_off,colA_size,colA_base,colA_scale,_colA);
          double Y = ary.datad(bits,i,rowsize,colB_off,colB_size,colB_base,colB_scale,_colB);
          double Xa = (X-_Xbar);
          double Ya = (Y-_Ybar);
          _XXbar += Xa*Xa;
          _YYbar += Ya*Ya;
          _XYbar += Xa*Ya;
        }
        break;
      }
    }

    public void reduce( DRemoteTask rt ) {
      COV_Task  cov = (COV_Task)rt;
      switch( _pass ) {
      case 1:
        _sumX += cov._sumX ;
        _sumY += cov._sumY ;
        break;
      case 2:
        _XXbar += cov._XXbar;
        _YYbar += cov._YYbar;
        _XYbar += cov._XYbar;
        break;
      }
    }
  }
}

