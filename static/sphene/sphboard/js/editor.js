var myeditor, ifm;
var content;
var isIE = /msie|MSIE/.test(navigator.userAgent);
var browser = isIE || window.opera;
var tr;

function rep(re, str) {
    content = content.replace(re, str);
}

function html2bbcode() {
    // example: <strong> to [b]
    rep(/#000000/gi,"black");
    rep(/#FF0000/gi,"red");
    rep(/#0000FF/gi,"blue");
    rep(/#008000/gi,"green");
    rep(/#FFA500/gi,"orange");
    rep(/#FF00FF/gi,"fuchsia");
    rep(/#00FFFF/gi,"aqua");
    rep(/#00FF00/gi,"lime");
    rep(/#800000/gi,"maroon");
    rep(/#800080/gi,"purple");
    rep(/#000080/gi,"navy");
    rep(/#008080/gi,"teal");
    rep(/rgb\(0,\s?0,\s?,0\)/gi,"black");
    rep(/rgb\(255,\s?0,\s?,0\)/gi,"red");
    rep(/rgb\(0,\s?0,\s?,255\)/gi,"blue");
    rep(/rgb\(0,\s?128,\s?,0\)/gi,"green");
    rep(/rgb\(255,\s?165,\s?,0\)/gi,"orange");
    rep(/rgb\(255,\s?0,\s?,255\)/gi,"fuchsia");
    rep(/rgb\(0,\s?255,\s?,255\)/gi,"aqua");
    rep(/rgb\(0,\s?255,\s?,0\)/gi,"lime");
    rep(/rgb\(128,\s?0,\s?,0\)/gi,"maroon");
    rep(/rgb\(128,\s?0,\s?,128\)/gi,"purple");
    rep(/rgb\(0,\s?0,\s?,128\)/gi,"navy");
    rep(/rgb\(0,\s?128,\s?,128\)/gi,"teal");

    rep(/<img\s[^<>]*?src=\"?([^<>]*?)\"?(\s[^<>]*)?\/?>/gi,"[img]$1[/img]");
    rep(/<\/(strong|b)>/gi,"[/b]");
    rep(/<(strong|b)(\s[^<>]*)?>/gi,"[b]");
    rep(/<\/(em|i)>/gi,"[/i]");
    rep(/<(em|i)(\s[^<>]*)?>/gi,"[i]");
    rep(/<\/u>/gi,"[/u]");
    rep(/<u(\s[^<>]*)?>/gi,"[u]");
    rep(/<br(\s[^<>]*)?>/gi,"\n");
    rep(/<p(\s[^<>]*)?>/gi,"");
    rep(/<\/p>/gi,"\n");
    rep(/&nbsp;/gi," ");
    rep(/&quot;/gi,"\"");
    rep(/&amp;/gi,"&");
    var sc, sc2;
    do {
      sc = content;
      rep(/<font\s[^<>]*?color=\"?([^<>]*?)\"?(\s[^<>]*)?>([^<>]*?)<\/font>/gi,"[color=$1]$3[/color]");
      if(sc==content)
        rep(/<font[^<>]*?>([^<>]*?)<\/font>/gi,"$1");
      rep(/<a\s[^<>]*?href=\"?([^<>]*?)\"?(\s[^<>]*)?>([^<>]*?)<\/a>/gi,"[url=$1]$3[/url]");
      rep(/<pre\s[^<>]*?class=\"?code\"?[^<>]*?>([^<>]*?)<\/pre>/gi,"[code]$1[/code]");
      sc2 = content;
      rep(/<blockquote\s[^<>]*?class=\"?memberquote\"?[^<>]*?id=\"?([^<>\"]*)\"?>([^<>]*?)<\/blockquote>/gi,"[quote$1]$2[/quote]");
      if(sc2==content)
        rep(/<blockquote\s[^<>]*?class=\"?memberquote\"?[^<>]*?>([^<>]*?)<\/blockquote>/gi,"[quote]$1[/quote]");
      rep(/<span\s[^<>]*?style=\"?font-weight: ?bold;?\"?\s*([^<]*?)<\/span>/gi,"[b]<span style=$1</span>[/b]");
      rep(/<span\s[^<>]*?style=\"?font-weight: ?normal;?\"?\s*([^<]*?)<\/span>/gi,"<span style=$1</span>");
      rep(/<span\s[^<>]*?style=\"?font-style: ?italic;?\"?\s*([^<]*?)<\/span>/gi,"[i]<span style=$1</span>[/i]");
      rep(/<span\s[^<>]*?style=\"?font-style: ?normal;?\"?\s*([^<]*?)<\/span>/gi,"<span style=$1</span>");
      rep(/<span\s[^<>]*?style=\"?text-decoration: ?underline;?\"?\s*([^<]*?)<\/span>/gi,"[u]<span style=$1</span>[/u]");
      rep(/<span\s[^<>]*?style=\"?text-decoration: ?none;?\"?\s*([^<]*?)<\/span>/gi,"<span style=$1</span>");
      rep(/<span\s[^<>]*?style=\"?color: ?([^<>]*?);\"?\s*([^<]*?)<\/span>/gi,"[color=$1]<span style=$2</span>[/color]");
      rep(/<span\s[^<>]*?style=\"?\"?>([^<>]*?)<\/span>/gi, "$1");
    }while(sc!=content)
    rep(/<[^<>]*>/,"");
    rep(/&lt;/gi,"<");
    rep(/&gt;/gi,">");
    
    //clean up empty tags
    do {
      sc = content;
      rep(/\[b\]\[\/b\]/gi, "");
      rep(/\[i\]\[\/i\]/gi, "");
      rep(/\[u\]\[\/u\]/gi, "");
      rep(/\[quote\]\[\/quote\]/gi, "");
      rep(/\[code\]\[\/code\]/gi, "");
      rep(/\[url=([^\]]+)\]\[\/url\]/gi, "");
      rep(/\[img\]\[\/img\]/gi, "");
      rep(/\[color=([^\]]*?)\]\[\/color\]/gi, "");
    }while(sc!=content)
}

function bbcode2html() {
    // example: [b] to <strong>
    rep(/--- Last Edited by [\s\S]*? ---/gi,"");
    rep(/\n/gi,"<br />");
    if(browser) {
      rep(/\[b\]/gi,"<strong>");
      rep(/\[\/b\]/gi,"</strong>");
      rep(/\[i\]/gi,"<em>");
      rep(/\[\/i\]/gi,"</em>");
      rep(/\[u\]/gi,"<u>");
      rep(/\[\/u\]/gi,"</u>");
    }else {
      rep(/\[b\]/gi,"<span style=\"font-weight: bold;\">");
      rep(/\[i\]/gi,"<span style=\"font-style: italic;\">");
      rep(/\[u\]/gi,"<span style=\"text-decoration: underline;\">");
      rep(/\[\/(b|i|u)\]/gi,"</span>");
    }
    rep(/\[img\]([\s\S]*?)\[\/img\]/gi,"<img src=\"$1\" />");
    var sc;
    do {
      sc = content;
      rep(/\[url=([^\]]+)\]([\s\S]*?)\[\/url\]/gi,"<a href=\"$1\">$2</a>");
      rep(/\[url\]([\s\S]*?)\[\/url\]/gi,"<a href=\"$1\">$1</a>");
      if(browser) {
        rep(/\[color=([^\]]*?)\]([\s\S]*?)\[\/color\]/gi,"<font color=\"$1\">$2</font>");
      }else {
        rep(/\[color=([^\]]*?)\]([\s\S]*?)\[\/color\]/gi,"<span style=\"color: $1;\">$2</span>");
      }
      rep(/\[code\]([\s\S]*?)\[\/code\]/gi,"<pre class=\"code\">$1</pre>&nbsp;");
      rep(/\[quote([^\]]*?)\]([\s\S]*?)\[\/quote\]/gi,"<blockquote class=\"memberquote\" id=\"$1\">$2</blockquote>&nbsp;");
    }while(sc!=content)
}

function doCheck() {
  content = myeditor.body.innerHTML;
  html2bbcode();
  document.getElementById('id_body').value = content;
}

function doQC(m){
  var w = ifm.contentWindow;
  var s;
  w.focus();
  if (w.getSelection) {
    s = w.getSelection();
    var r;
    if (s.getRangeAt)
      r = s.getRangeAt(0);
    else { // Safari!
      r = myeditor.createRange();
      r.setStart(s.anchorNode,s.anchorOffset);
      r.setEnd(s.focusNode,s.focusOffset);
    }
    if(m==1) {
      var n = myeditor.createElement('blockquote');
      n.className = 'memberquote';
      r.surroundContents(n);
    }else { //code
      var n = myeditor.createElement('pre');
      n.className = 'code';
      r.surroundContents(n);
    }
  }else if (w.document.selection) { //For IE
    var s = w.document.selection.createRange();
    if(m==1){
      s.pasteHTML('<blockquote class="memberquote">'+s.htmlText+'</blockquote>');
    }else {
      s.pasteHTML('<pre class="code">'+s.htmlText+'</pre>');
    }
  }else {
    alert('Not supported on your browser!');
    return;
  }
}

function doClick(command) {
  ifm.contentWindow.focus();
  myeditor.execCommand(command, false, null); 
}

function doColor(color) {
  ifm.contentWindow.focus();
  if(isIE)
    tr.select();
  myeditor.execCommand('forecolor', false, color);
}

function doLink() {
  ifm.contentWindow.focus();
  var mylink = prompt("Enter a URL:", "http://");
  if ((mylink != null) && (mylink != "")) {
    myeditor.execCommand("CreateLink",false,mylink);
  }
}
function doImage() {
  ifm.contentWindow.focus();
  myimg = prompt('Enter Image URL:', 'http://');
  if ((myimg != null) && (myimg != "")) {
    myeditor.execCommand('InsertImage', false, myimg);
  }
}

function insertSmiley(n){
  ifm.contentWindow.focus();
  if(n<10){n = '0'+n.toString();}else{n = n.toString();}
  myeditor.execCommand('InsertImage', false, editor_static + '/smilies/n0'+n+'.gif');
}

function switchBtn(e, on) {
  if(on) {
    e.className = 'bh';
    if (isIE)
      tr = ifm.contentWindow.document.selection.createRange();
  }else {
    e.className = 'bn';
  }
}