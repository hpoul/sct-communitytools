  var t = document.getElementById('id_body');
  content = t.innerHTML;
  var p = t.parentNode.previousSibling;
  var i, n;
  var a = new Array("doClick('undo')","doClick('redo')","doClick('bold')","doClick('italic')","doClick('underline')","doClick('RemoveFormat')","doLink()","doClick('unlink')","doImage()","doQC(1)","doQC(2)");
  var alt = new Array("undo","redo","bold","italic","underline","clear","link","unlink","picture","quote","code");
  var c = new Array("black","red","blue","green","orange","fuchsia","aqua","lime","maroon","purple","teal");

  var str = "<table><tr>";
  for(i=0;i<11;i++) {
    str += '<td><div class="bn" onmouseover="switchBtn(this, 1)" onmouseout="switchBtn(this, 0)" onclick="' + a[i] + '" style="cursor:pointer;"><img src="'+editor_static+'/images/' + alt[i] + '.gif" title="' + alt[i] + '" width=16 height=16></div></td>';
    if(i==1)
      str += '<td><div style="border:1px solid #BBBBBB;border-style:inset;height:18px;"></div></td>';
  }
  str += '<td><div style="border:1px solid #BBBBBB;border-style:inset;height:18px;"></div></td>';
  for(i=0;i<11;i++) {
    str += '<td><div class="bn" onmouseover="switchBtn(this, 1)" onmouseout="switchBtn(this, 0)" onclick="doColor(\'' + c[i] + '\')" style="cursor:pointer;"><div style="width:16px;height:16px;background-color:' + c[i] + ';"></div></div></td>';
  }
  str += '</tr></table><iframe id="rte" style="border:1px solid grey;width:100%;height:300px"></iframe><input type="hidden" id="id_body" name="body"/>';
  t.parentNode.innerHTML = str;

  str = p.innerHTML + '<div id="smilies"><table>';
  for(i=1;i<=24;i++) {
    if(i%3==1) {
      str += '<tr align="center" height="36">';
    }
    if(i<10){n = '0'+i.toString();}else{n = i.toString();}
    str += '<td valign="middle"><div class="bn" onmouseover="switchBtn(this, 1)" onmouseout="switchBtn(this, 0)" onclick="insertSmiley(' + i + ')" style="cursor:pointer;"><img src="'+editor_static+'/smilies/n0' + n + '.gif" width=30 border=0 height=30></div></td>';
    if(i%3==0) {
      str += '</tr>';
    }
  }
  p.innerHTML = str + '</table></div>';
  
  function init() {
    ifm = document.getElementById("rte");
    if(ifm) {
      myeditor = ifm.contentWindow.document;
      bbcode2html();
      myeditor.open();
      myeditor.write('<html><head><link rel="stylesheet" href="'+editor_static+'/styles/editor.css"/></head><body>' + content + '</body></html>');
      myeditor.close();
      myeditor.designMode = "on";
      if (myeditor.attachEvent){
        myeditor.attachEvent("onkeypress", kp);
      }else if(myeditor.addEventListener){
        myeditor.addEventListener("keypress",kp,true);
      }else{
        myeditor["onkeypress"] = kp;
      }
    }else
      setTimeout('init()', 100);
  }
  setTimeout('init()', 100);
