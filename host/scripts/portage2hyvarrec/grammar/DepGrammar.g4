grammar DepGrammar;

// To generate files run: antlr4 -Dlanguage=Python2 -visitor -no-listener DepGrammar.g4

options { tokenVocab=DepGrammarLexer; }


///////////////////////////////////////////////////////////
// MAIN

required: requiredEL* ;

requiredEL:
    NOT? use=ID                                       #requiredSIMPLE
  | condition LPAREN requiredEL* RPAREN               #requiredCONDITION
  | choice LPAREN requiredEL* RPAREN                  #requiredCHOICE
  | LPAREN requiredEL* RPAREN                         #requiredINNER
  ;

depend: dependEL* ;

dependEL:
    (NOT NOT?)? atom                               #dependSIMPLE
  | condition LPAREN dependEL* RPAREN                 #dependCONDITION
  | choice LPAREN dependEL* RPAREN                    #dependCHOICE
  | LPAREN dependEL* RPAREN                           #dependINNER
  ;

choice: OR | ONEMAX | XOR ;
condition: NOT? use=ID IMPLIES;

atom:
  version_op? category=ID DIV package=ID TIMES? (COLON slot_spec)? (LBRACKET selection (COMMA selection)* RBRACKET)?
  ;

// != is not needed since the ! is matched in dependSIMPLE
version_op: LEQ | LT | GT | GEQ | EQ | REV ;



slot_spec:
    slot=ID                                   #slotSIMPLE
  | slot=ID DIV subslot=ID                    #slotFULL
  // why is there a ? for the id?
  | slot=ID? EQ                               #slotEQ
  | TIMES                                     #slotSTAR
  ;

selection: prefix? use=ID preference? suffix? ;
prefix: NOT | MINUS | PLUS ;
preference: LPAREN (PLUS | MINUS) RPAREN ;
suffix: IMPLIES | EQ ;





