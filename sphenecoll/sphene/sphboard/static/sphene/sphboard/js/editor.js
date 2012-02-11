var myeditor, ifm;
var content;
var isIE = /msie|MSIE/.test(navigator.userAgent);
var isChrome = /Chrome/.test(navigator.userAgent);
var isSafari = /Safari/.test(navigator.userAgent) && !isChrome;
var browser = isIE || window.opera;
var tr;
var enter=0;

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
	rep(/#008080/gi,"teal");
	rep(/rgb\(0,\s?0,\s?0\)/gi,"black");
	rep(/rgb\(255,\s?0,\s?0\)/gi,"red");
	rep(/rgb\(0,\s?0,\s?255\)/gi,"blue");
	rep(/rgb\(0,\s?128,\s?0\)/gi,"green");
	rep(/rgb\(255,\s?165,\s?0\)/gi,"orange");
	rep(/rgb\(255,\s?0,\s?255\)/gi,"fuchsia");
	rep(/rgb\(0,\s?255,\s?255\)/gi,"aqua");
	rep(/rgb\(0,\s?255,\s?0\)/gi,"lime");
	rep(/rgb\(128,\s?0,\s?0\)/gi,"maroon");
	rep(/rgb\(128,\s?0,\s?128\)/gi,"purple");
	rep(/rgb\(0,\s?128,\s?128\)/gi,"teal");

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
	rep(/<div([^<>]*)>/gi,"\n<span$1>");
	rep(/<\/div>/gi,"</span>\n");
	rep(/&nbsp;/gi," ");
	rep(/&quot;/gi,"\"");
	rep(/&amp;/gi,"&");
	var sc, sc2;
	do {
		sc = content;
		rep(/<font\s[^<>]*?color=\"?([^<>]*?)\"?(\s[^<>]*)?>([^<>]*?)<\/font>/gi,"[color=$1]$3[/color]");
		if(sc==content)
			rep(/<font[^<>]*>([^<>]*?)<\/font>/gi,"$1");
		rep(/<a\s[^<>]*?href=\"?([^<>]*?)\"?(\s[^<>]*)?>([^<>]*?)<\/a>/gi,"[url=$1]$3[/url]");
		sc2 = content;
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?font-weight: ?bold;?\"?\s*([^<]*?)<\/\1>/gi,"[b]<$1 style=$2</$1>[/b]");
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?font-weight: ?normal;?\"?\s*([^<]*?)<\/\1>/gi,"<$1 style=$2</$1>");
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?font-style: ?italic;?\"?\s*([^<]*?)<\/\1>/gi,"[i]<$1 style=$2</$1>[/i]");
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?font-style: ?normal;?\"?\s*([^<]*?)<\/\1>/gi,"<$1 style=$2</$1>");
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?text-decoration: ?underline;?\"?\s*([^<]*?)<\/\1>/gi,"[u]<$1 style=$2</$1>[/u]");
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?text-decoration: ?none;?\"?\s*([^<]*?)<\/\1>/gi,"<$1 style=$2</$1>");
		rep(/<(span|blockquote|pre)\s[^<>]*?style=\"?color: ?([^<>]*?);\"?\s*([^<]*?)<\/\1>/gi,"[color=$2]<$1 style=$3</$1>[/color]");
		rep(/<(blockquote|pre)\s[^<>]*?style=\"?\"? (class=|id=)([^<>]*)>([^<>]*?)<\/\1>/gi,"<$1 $2$3>$4</$1>");
		rep(/<span\s[^<>]*?style=\"?\"?>([^<>]*?)<\/span>/gi, "$1");
		if(sc2==content) {
			rep(/<span[^<>]*>([^<>]*?)<\/span>/gi, "$1");
			sc2 = content;
			rep(/<pre\s[^<>]*?class=\"?code\"?[^<>]*?>([^<>]*?)<\/pre>/gi,"[code]$1[/code]");
			if(sc2==content) {
				rep(/<blockquote\s[^<>]*?class=\"?memberquote\"?[^<>]*?id=\"?([^<>\"]*)\"?>([^<>]*?)<\/blockquote>/gi,"[quote$1]$2[/quote]");
				if(sc2==content) {
					rep(/<blockquote\s[^<>]*?id=\"?([^<>\"]*?)\"? class=\"?memberquote\"?[^<>]*?>([^<>]*?)<\/blockquote>/gi,"[quote$1]$2[/quote]");
					if(sc2==content)
						rep(/<blockquote\s[^<>]*?class=\"?memberquote\"?[^<>]*?>([^<>]*?)<\/blockquote>/gi,"[quote]$1[/quote]");
				}
			}
		}
	}while(sc!=content)
	rep(/<[^<>]*>/gi,"");
	rep(/&lt;/gi,"<");
	rep(/&gt;/gi,">");
	
	do {
		sc = content;
		rep(/\[(b|i|u)\]\[quote([^\]]*)\]([\s\S]*?)\[\/quote\]\[\/\1\]/gi, "[quote$2][$1]$3[/$1][/quote]");
		rep(/\[color=([^\]]*)\]\[quote([^\]]*)\]([\s\S]*?)\[\/quote\]\[\/color\]/gi, "[quote$2][color=$1]$3[/color][/quote]");
		rep(/\[(b|i|u)\]\[code\]([\s\S]*?)\[\/code\]\[\/\1\]/gi, "[code][$1]$2[/$1][/code]");
		rep(/\[color=([^\]]*)\]\[code\]([\s\S]*?)\[\/code\]\[\/color\]/gi, "[code][color=$1]$2[/color][/code]");
	}while(sc!=content)

	//clean up empty tags
	do {
		sc = content;
		rep(/\[b\]\[\/b\]/gi, "");
		rep(/\[i\]\[\/i\]/gi, "");
		rep(/\[u\]\[\/u\]/gi, "");
		rep(/\[quote[^\]]*\]\[\/quote\]/gi, "");
		rep(/\[code\]\[\/code\]/gi, "");
		rep(/\[url=([^\]]+)\]\[\/url\]/gi, "");
		rep(/\[img\]\[\/img\]/gi, "");
		rep(/\[color=([^\]]*)\]\[\/color\]/gi, "");
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

function stopEvent(evt){
	evt || window.event;
	if (evt.stopPropagation){
		evt.stopPropagation();
		evt.preventDefault();
	}else if(typeof evt.cancelBubble != "undefined"){
		evt.cancelBubble = true;
		evt.returnValue = false;
	}
	return false;
}

function kp(e){
	if(isIE)
		var k = e.keyCode;
	else
		var k = e.which;
	if(k==13) {
		if(enter) {
			enter = 0;
			if(splitQuote()){
				stopEvent(e);
				return false;
			}
		}
		else if(isSafari) {
			if(splitQuote()){
				stopEvent(e);
				return false;
			}
		}else
			enter = 1;

		if(isIE) {
			var r = myeditor.selection.createRange();
			r.pasteHTML('<br>');
			if(r.move('character'))
				r.move('character',-1);
			r.select();
			stopEvent(e);
			return false;
		}
	}else
		enter = 0;
}

function splitQuote(){
	var w = ifm.contentWindow;
	var s;
	w.focus();
	if (w.getSelection) {
		s = w.getSelection();
		var r;
		if (s.getRangeAt)
			r = s.getRangeAt(0);
		else {
			r = myeditor.createRange();
			r.setStart(s.anchorNode,s.anchorOffset);
			r.setEnd(s.focusNode,s.focusOffset);
		}
		var q = r.startContainer;
		var f=0;
		while(q!='[object HTMLBodyElement]') {
			if(q=='[object HTMLQuoteElement]' || q=='[object HTMLBlockquoteElement]'){
				f=1;
				break;
			}
			q = q.parentNode;
		}
		if(f) {
			if(!r.collapsed)
				r.deleteContents();
			var c = r.startContainer;
			var o = r.startOffset;
			r.selectNodeContents(q);
			var r0 = myeditor.createRange();
			r0.setStart(r.startContainer,r.startOffset);
			r0.setEnd(c,o);
			r.setStart(c,o);
			if(r=='') {
				if(window.opera||isChrome||isSafari)
					q.parentNode.insertBefore(myeditor.createTextNode('---'),q.nextSibling);
				else {
					n = myeditor.createTextNode(' ');
					q.parentNode.insertBefore(n,q.nextSibling);
					r.setStart(n,0);
					r.setEnd(n,0);
				}
			}else {
				if(r0!='') {
					var n = myeditor.createElement('blockquote');
					n.id = q.id;
					n.className = 'memberquote';
					n.appendChild(r0.extractContents());
					q.parentNode.insertBefore(n,q);
				}
				if(window.opera||isChrome||isSafari)
					q.parentNode.insertBefore(myeditor.createTextNode('---'),q);
				else {
					n = myeditor.createTextNode(' ');
					q.parentNode.insertBefore(n,q);
					r.setStart(n,0);
					r.setEnd(n,0);
				}
			}
			return true;
		}
	}else if (w.document.selection) {
		var s = w.document.selection.createRange();
		var q = s.parentElement();
		var f=0;
		while(q.nodeName!='BODY') {
			if(q.nodeName=='BLOCKQUOTE'){
				f=1;
				break;
			}
			q = q.parentNode;
		}
		if(f) {
			if(s.text!='')
				s.pasteHTML('');
			var r = s.duplicate();
			r.moveToElementText(q);
			s.setEndPoint('EndToEnd',r);
			r.setEndPoint('EndToStart',s);
			if(r.text!='') {
				var n1 = myeditor.createElement('blockquote');
				n1.id = q.id;
					n1.className = 'memberquote';
				n1.innerHTML = r.htmlText;
			}else
				var n1 = myeditor.createTextNode('');
			if(s.text!='') {
				var n2 = myeditor.createElement('blockquote');
				n2.id = q.id;
				n2.className = 'memberquote';
				n2.innerHTML = s.htmlText;
			}else
				var n2 = myeditor.createTextNode('');
			var n3 = myeditor.createElement('span');
			n3.appendChild(myeditor.createTextNode(' '));
			var p = q.parentNode;
			p.insertBefore(n2,q);
			p.insertBefore(n3,n2);
			p.insertBefore(n1,n3);
			p.removeChild(q);
			r.moveToElementText(n3);
			r.move('character',-1);
			r.select();
			return true;
		}
	}
	return false;
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
		else {
			r = myeditor.createRange();
			r.setStart(s.anchorNode,s.anchorOffset);
			r.setEnd(s.focusNode,s.focusOffset);
		}
		if(m==1) {
			var n = myeditor.createElement('blockquote');
			n.className = 'memberquote';
			r.surroundContents(n);
		}else {
			var n = myeditor.createElement('pre');
			n.className = 'code';
			r.surroundContents(n);
		}
	}else if (w.document.selection) {
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
