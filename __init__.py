import logging
from tkinter import *
from tkinter import ttk
import traceback
from time import time as t_time

__all__ = ('UIParser', 'ParserException')
logger = logging.getLogger(__name__)

class UIParserBase(object):
    '''The UIParser is responsible for creating a :class:`Parser` for parsing a
    tkui file, merging the results into its internal rules, templates, etc.
    '''
    filename = None
    master = None
    __prev_widget_level = None
    sourcecode = []
    __filtered_sourcecode = []
    __indentation = None
    __previous_widget = None
    __current_widget = None
    __content, __layout = None, None
    __prev_line_indentation = 0
    __widget_with_level = {}
    __widget_layout = {}
    __created_widget_name = {}
    __style_prop = {}
    __config_prop = {}
    __pack_prop = {}
    __grid_columnconfigure = [False, None]
    __grid_rowconfigure = [False, None]
    ## Widgets
    __ui_data_class = {
        "Label": Label,
        "TLabel": ttk.Label,
        "LabelFrame": LabelFrame,
        "TLabelFrame": ttk.LabelFrame,
        "Entry": Entry,
        "TEntry": ttk.Entry,
        "Frame": Frame,
        "TFrame": ttk.Frame,
        "Button": Button,
        "TButton": Button,
        "Checkbutton": Checkbutton,
        "TCheckbutton": ttk.Checkbutton,
        "Menubutton": Menubutton,
        "TMenubutton": ttk.Menubutton,
        "PanedWindow": PanedWindow,
        "TPanedWindow": ttk.PanedWindow,
        "Radiobutton": Radiobutton,
        "TRadiobutton": ttk.Radiobutton,
        "Scale": Scale,
        "TScale": ttk.Scale,
        "Scrollbar": Scrollbar,
        "TScrollbar": ttk.Scrollbar,
        "Combobox": ttk.Combobox,
        "Notebook": ttk.Notebook,
        "Progressbar": ttk.Progressbar,
        "Separator": ttk.Separator,
        "Sizegrip": ttk.Sizegrip,
        "Treeview": ttk.Treeview,
    }

    __ttk_widget_list = [
        "TLabel", "TLabelFrame", "TEntry", "TFrame", "TButton", "TCheckbutton",
        "TMenubutton", "TPanedWindow", "TRadiobutton", "TScale", "TScrollbar",
        "Combobox", "Notebook", "Progressbar", "Separator", "Sizegrip", "Treeview"
    ]

    __tstyle_props = ['activebackground', 'activeforeground', 'bd', 'bg','disabledforeground', 
        'fg', 'font','height', 'highlightbackground', 'highlightcolor', 'highlightthickness',
    ]

    __widget_pack_props = [
        "fill", "expand", "anchor", "sticky", "padx", "pady", "p_height", "p_width", "bordermode",
        "relheight", "relwidth", "relx", "rely", "x", "y", "ipadx", "ipady", "row", "rowspan", "column",
        "columnspan", "side"
    ]

    def __init__(self):
        super(UIParserBase, self).__init__()

    def load_file(self, filename, master, encoding='utf-8', **kwargs):
        """
        Insert a file into the language builder and return the root widget
        (if defined) of the tkui file.

        :parameters:
            `filename`: File where the designer stated,
            `encoding`: File charcter encoding. Defaults to utf-8,
        """
        try:
            self.filename = filename
            with open(filename, encoding=encoding) as fin:
                return self.load_string(fin.readlines(), master)
        except:
            logger.error("Below Exception occurred.\n", exc_info=True)
            

    def load_string(self, content, master):
        """
        Load String reprenstation of the UI Designer file
        :parameters:
            `content`: File charcter encoding. Defaults to utf-8,
        """
        try:
            # self.tree_root = ET.fromstring(content)
            self.master = master
            self.sourcecode = content
            self.ttk_style = ttk.Style(self.master)
            self.__filter_content()

            self.__indentation = len(self.__filtered_sourcecode[1]) - len(self.__filtered_sourcecode[1].lstrip(' \t'))
            if self.__indentation == 0:
                raise ParserException(self, 1, "Code should be inside one Root, either a Frame or LabelFrame")
            self.__parse()
            return self.__created_widget_name
        except:
            logger.error("Below Exception occurred.\n", exc_info=True)

    def __filter_content(self):
        """
        Filter the content, Remove the Comments, Whitespace, Replace Tabs with spaces
        """
        try:
            for line in self.sourcecode:
                # Remove space from end
                without_ending_space = line.replace("\n", "")
                #Replace Tab with 4 spaces
                without_tab = without_ending_space.replace("\t", "    ")
                # Remove comment
                # Find '#' symbol
                pos_hash = without_tab.find("#")
                pos_hash = pos_hash if pos_hash > 0 else None
                l2 = without_tab[:pos_hash]
                if bool(l2.strip()):
                    self.__filtered_sourcecode.append(l2)
        except:
            logger.error("Below Exception occurred.\n", exc_info=True)

    def __parse(self):
        """
        Parsing the UI Designer into the tkinter class widget.
        """
        try:
            prev_line_indentation = None
            for _line, line_content in enumerate(self.__filtered_sourcecode):
                #Get the current Line Indentation
                line_indentation = len(line_content) - len(line_content.lstrip(' \t'))

                #If Lineindentation is wrong.
                if line_indentation > 0 and line_indentation % self.__indentation != 0:
                    raise ParserException(self, _line, f"Invalid Indetation, should be multiply of {self.__indentation} spaces")
                content_with_classname = True if line_content.rstrip()[-1] == ":" else False

                if not(content_with_classname) and prev_line_indentation != line_indentation and prev_line_indentation is not None:
                    raise ParserException(self, _line, f"Invalid Indetation, Indentation should only be after new class.")

                level = int(line_indentation / self.__indentation)
                if content_with_classname:
                    if self.__current_widget is not None:
                        if level > 0:
                            if self.__prev_widget_level == level :
                                used_layout = self.__widget_layout[str(level - 1)]
                            elif level < self.__prev_widget_level:
                                used_layout = self.__widget_layout[str(self.__prev_widget_level - 1)]
                            else:
                                if level > 1:
                                    used_layout = self.__widget_layout[str(level - 2)]
                                else:
                                    used_layout = "PackLayout"
                        else:
                            used_layout = "PackLayout"

                        if used_layout == "PackLayout":
                            self.__current_widget.pack(**self.__pack_prop)
                        elif used_layout == "GridLayout":
                            self.__current_widget.grid(**self.__pack_prop)
                        elif used_layout == "PlaceLayout":
                            self.__current_widget.place(**self.__pack_prop)
                        else:
                            raise ParserException(self, _line, f"Invalid Layout managment '{used_layout}' used, should be PackLayout, GridLayout or PlaceLayout.")
                        
                        self.__current_widget.config(**self.__config_prop)
                        if bool(self.__style_prop):
                            ct_in_ms = int(t_time() * 1000)
                            style_name = f"tstyle_{ct_in_ms}.{self.__content}"
                            self.ttk_style.configure(style_name, **self.__style_prop)
                            self.__current_widget.config(style=style_name)
                        #Grid column configure
                        if self.__widget_layout.get(str(level - 1),"PackLayout") == "GridLayout":
                            if self.__grid_columnconfigure[0]:
                                self.__current_widget.columnconfigure(self.__grid_columnconfigure[1], weight = 1)
                            if self.__grid_rowconfigure[0]:
                                self.__current_widget.rowconfigure(self.__grid_rowconfigure[1], weight = 1)
                    self.__prev_widget_level = level
                    ##Resetting the Props
                    self.__reset()

                    content_with_layout = line_content.rstrip()[:-1].split("@")
                    if len(content_with_layout) == 2:
                        self.__content, self.__layout = content_with_layout[0].strip(), content_with_layout[1].strip()
                    else:
                        self.__content, self.__layout = content_with_layout[0].strip(), 'PackLayout'

                    self.__widget_layout[str(level)] = self.__layout

                    __class_ui = self.__ui_data_class.get(self.__content)
                    if __class_ui is None:
                        raise ParserException(self, _line, f"Invalid Classname {self.__content}. Should be a valid tkinter widget.")

                    if self.__current_widget is None:
                        self.__current_widget = __class_ui(self.master)
                        self.__widget_with_level["0"] = self.__current_widget

                    else:
                        if line_indentation > self.__prev_line_indentation:
                            self.__prev_line_indentation = line_indentation
                            self.__previous_widget = self.__current_widget
                            self.__previous_widget.pack(**self.__pack_prop)
                            
                            self.__current_widget = __class_ui(self.__previous_widget)
                            self.__widget_with_level[str(level)] = self.__current_widget
                            
                        elif line_indentation < self.__prev_line_indentation:
                            self.__prev_line_indentation = line_indentation
                            prev_level = level - 1 if level > 0 else 0
                            self.__previous_widget = self.__widget_with_level[str(prev_level)]
                            self.__current_widget = __class_ui(self.__previous_widget)
                            self.__widget_with_level[str(level)] = self.__current_widget
            
                        else:
                            self.__current_widget = __class_ui(self.__previous_widget)

                else:
                    _prop_name, _prop_value = [x.strip() for x in line_content.split(":")]
                    
                    if self.__current_widget is not None:
                        # if _prop_name == "text":
                        #     self.__current_widget.config(text=_prop_value)
                        if _prop_name in self.__tstyle_props:
                            if self.__content in self.__ttk_widget_list:
                                self.__style_prop[_prop_name] = _prop_value
                            else:
                                self.__config_prop[_prop_name] = _prop_value
                        elif _prop_name in self.__widget_pack_props:
                            if _prop_name in ("padx", "pady", "ipadx", "ipady") and _prop_value.find(",") > -1:
                                _prop_value = [x.strip() for x in _prop_value.split(",") if x.strip() != ""]
                            self.__pack_prop[_prop_name] = _prop_value
                        else:
                            if _prop_name == "name":
                                self.__created_widget_name[_prop_value] = self.__current_widget
                            elif _prop_name == "grid_columnconfigure":
                                self.__grid_columnconfigure = [True, int(_prop_value)]
                            elif _prop_name == "grid_rowconfigure":
                                self.__grid_rowconfigure = [True, int(_prop_value)]
                            else:
                                if _prop_name == "font":
                                    _prop_value = [x.strip() for x in _prop_value.split(",") if x.strip() != ""]
                                self.__config_prop[_prop_name] = _prop_value
                
                #Setting the prev line indentation
                prev_line_indentation = None if content_with_classname else line_indentation

            if self.__current_widget is not None:
                self.__current_widget.pack(**self.__pack_prop)
        
        except:
            logger.error("Below Exception occurred.\n", exc_info=True)

    def __reset(self):
        """
        Private function: Resetting the widgets and Props
        """
        try:
            ##Resetting the Props
            self.__pack_prop = {}
            self.__config_prop = {}
            self.__style_prop = {}
            self.__grid_columnconfigure = [False, None]
            self.__grid_rowconfigure = [False, None]
            logger.debug("Property Reset has been completed.")
        except:
            logger.error("Below Exception occurred.\n", exc_info=True)
        

class ParserException(Exception):
    '''Exception raised when something wrong happened in a designer file.
    '''
    def __init__(self, context, line, message, cause=None):
        self.filename = context.filename or '<inline>'
        self.line = line
        sourcecode = context.sourcecode
        sc_start = max(0, line - 2)
        sc_stop = min(len(sourcecode), line + 3)
        sc = ['...']
        for x in range(sc_start, sc_stop):
            if x == line:
                sc += ['>> %4d:%s' % (line + 1, sourcecode[line])]
            else:
                sc += ['   %4d:%s' % (x + 1, sourcecode[x])]
        sc += ['...']
        sc = '\n'.join(sc)

        message = 'Parser: File "%s", line %d:\n%s\n%s' % (
            self.filename, self.line + 1, sc, message)
        if cause:
            message += '\n' + ''.join(traceback.format_tb(cause))

        super(ParserException, self).__init__(message)

#: Main instance of a :class:`UIParserBase`.
UIParser = UIParserBase()
