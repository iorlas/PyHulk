#Gamma it's like a gamma bomb, which pretty complicated for most people, but this is what made the Hunk

import logging

#TODO: check for debug flag and update logger
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("Gamma")

import tokenize, token
import codecs, cStringIO, encodings, re
from encodings import utf_8
import sys, traceback, os

TAB_SIZE = 4
TAB_PATTERN = '    '

def eager_exit(code):
    log.error("Emergency exit. See information below.")
    print '\nIGNORE NEXT MESSAGES'
    sys.exit(code)

def trace_last_exception():
    print '*'*64
    traceback.print_exc(file=sys.stdout)
    print '*'*64

def shift_text(text, offset_line_pattern):
    return '\n'.join(map(lambda x: offset_line_pattern + x, text.split("\n")))

def is_not_whitespaced_line(string):
    return not re.match("^\ *\n\Z", string)


# def translate(readline):
#     previous_name = ""
#     for type, name, one, two, three in tokenize.generate_tokens(readline):
#         print "type: '%s', name: '%s', one: '%s', two: '%s', three: '%s'" %(type, name, one, two, three)
#         if type ==tokenize.NAME and name =='describe':
#             yield tokenize.NAME, 'class'
#         else:
#             yield type,name
#         previous_name = name

# def tokenize_string(string):
#     r = []
#     tokens = tokenize.generate_tokens(cStringIO.StringIO(string).readline)
#     for token_type, token_name,_,_,_ in tokens:
#         r.append((token_type, token_name))
#     return r


#generator of stream readers
def generate_parser(dsl_path):
    log.debug("New reader creating...")

    #main class, which called in the deeps of python as filter for code
    class StreamReader(utf_8.StreamReader):
        def __init__(self, *args, **kwargs):
            #save file name for debug
            self.file_name = os.path.basename(args[0].name)

            #TODO: Inherit options from root logger(see top of file)
            self.log = logging.getLogger("Gamma>"+self.dsl_path+">"+self.file_name)

            #we need to init root streamer
            codecs.StreamReader.__init__(self, *args, **kwargs)
            self.log.debug("Root UTF8 reader initiated")
            
            self.log.debug("New reader initiated")
            
            #yeah, it isn't lazy, but we can allocate enough ram for this simple file, isn't?
            self.log.debug("Starting mutator")
            try:
                data = self.mutate_it(self.dsl_path, self.stream.read())
            except Exception as e:
                trace_last_exception()
                self.log.debug("Inner logic exception. Exiting.")
                eager_exit(1)

            self.log.debug("It's alive!")
            #data = tokenize.untokenize(translate(self.stream.readline))

            self.log.debug("Parsing complete, sending it to Python")
            print self.file_name, len(data)
            print '-'*64
            print data
            print '-'*64
            self.stream = cStringIO.StringIO(str(data))
            
        #general mutator function
        def mutate_it(self, current_dsl_path, source):
            self.log.debug("Loading DSL module "+current_dsl_path)
            try:
                dsl = __import__(dsl_path)
            except ImportError as e:
                self.log.error("DSL cannot be found by path '%s'"%(current_dsl_path))
                eager_exit(1)
            
            result_code = u"" #this keeps result of processing

            #keeps tokenized code
            #tokenized_result_code = []

            #pre-code
            if hasattr(dsl, 'before') and callable(dsl.before):
                result_code += dsl.before()["code"]
                #tokenized_result_code += tokenize_string(dsl.before()["code"])
                
            #state variables
            state_stack = [] #tempary
            state_level = 0 #0 - root
            state_last_line = 0 #keeps current line num for some logic
            state_found = False #keeps state of work. True if current line worked out.
            state_stop_line = False #keeps state of user defined behavior for current line.
                                    #True if current line worked out and we dont need to work with its next tokens.
            state_last_line_str = u""

            #general tokens cycle
            for token_type, token_name, start, end, line in tokenize.generate_tokens(cStringIO.StringIO(source).readline):

                #update navigation! harr!
                if token_type == token.INDENT:
                    state_level += 1
                if token_type == token.DEDENT:
                    state_level -= 1
                #print it for me!
                self.log.debug("Token %s, type %s, line %s. Level: %s, stack: %s."%(repr(token_name), tokenize.tok_name[token_type], repr(line), state_level, state_stack))
                if token_type is token.ERRORTOKEN:
                    self.log.warning("This is a ERROR Token! I believe you can handle it right.")

                #if previous line is not worked out - just insert it as it is
                if not state_found and state_last_line is not start[0] and not state_stop_line:
                    self.log.debug("Adding line %s as it is: %s"%(state_last_line, repr(state_last_line_str)))
                    result_code += state_last_line_str
                
                #reset some state things
                state_found = False

                #update some things for nagigation and smthng else
                if state_last_line != start[0]:
                    #skip check for first line, it's just a start! avoiding bug, also
                    if state_last_line is not 0:
                        state_stop_line = False #if it is a new line, it dont makes sense anymore, we can reset it

                #if this line locked - just skip it
                if state_stop_line:
                    continue
                
                #if it is *dent - skip, we can wait another token, cuz it can be another *dent!
                if token_type not in [token.DEDENT, token.INDENT]:
                    #working with blocks by rx
                    for block_rx in dsl.global_block_rx:

                        #trying to match current rx
                        r = block_rx["rx"].match(line)
                        
                        #if matched, work with it
                        if r:
                            self.log.debug("Block rx id%s %s matched at token %s (start: %s, end: %s), token type id: %s. Matched by line: %s. Result group: %s. Groups: %s."%
                                (block_rx["id"], repr(block_rx["rx_str"]), repr(token_name), start, end, tokenize.tok_name[token_type], repr([line]), repr(r.group()), r.groups()))

                            #call user function with full information
                            state = block_rx["func"](group = r.group(), groups=r.groups(), token=token_name,
                                line=line, position=start, level=state_level, ops_stack=state_stack)
                            
                            #okay, commit it
                            result_code += shift_text(state["code"], TAB_PATTERN*state_level)
                            #tokenized_result_code += tokenize_string(state["code"])

                            #do we really need to seek next tokens?
                            state_stop_line = state["stop"]
                        
                            #we dont need to search any other rx
                            state_found = True
                            break
                    
                    #if 404 - trying to use another rxes
                    if not state_found:
                        pass

                #update some things for nagigation and smthng else
                if state_last_line != start[0]:
                    #update state of last line
                    state_last_line = start[0]
                    state_last_line_str = line
            
            #post-code
            if hasattr(dsl, 'after') and callable(dsl.after):
                result_code += dsl.after()["code"]
                #tokenized_result_code += tokenize_string(dsl.after()["code"])
            
            #result_code = tokenize.untokenize(tokenized_result_code)

            #finish him!
            return result_code

    #save path to choosen dsl in the reader for future use
    StreamReader.dsl_path = dsl_path

    #return generated reader
    try:
        return StreamReader
    except Exception as e:
        trace_last_exception()
        eager_exit(1)
    finally:
        log.debug("New reader created")

#codecs hook
def search_function(name):
    log.debug("Catching '%s' codec name"%(name))

    #ignore not interesting encodings
    if not name.startswith("dsl-"):
        return None
    log.debug("'%s' codec name accepted as DSL '%s' invoking"%(name, name[len("dsl-"):]))
    
    #unicode FTW, we'll use UTF8 ending as base of DSL
    utf8 = encodings.search_function('utf8')
    log.debug("Original UTF8 encoding found, creating new codec with wrapper")
    return codecs.CodecInfo(
        name=name,
        encode = utf8.encode,
        decode = utf8.decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=utf8.incrementaldecoder,
        streamreader=generate_parser(name[4:]),
        streamwriter=utf8.streamwriter)

codecs.register(search_function) 
log.debug("DSL manager loaded")
