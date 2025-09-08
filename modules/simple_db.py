#
################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2025 Curt Timmerman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################
#
## SimpleDB - Very simple relational database
#
# Notes:
#   o Uses btree module for DB engine.
#   o JSON is the default row storage format
#   o USE_JSON = False for umsgpack row storage format (more compact)
#
################################################################################

## Required for load/dump
import json

USE_JSON = True

btree = None
dumps = None
loads = None

if USE_JSON :
    ## Use json module for row serialization
    print ("Using json module")
    try :
        import btree
        dumps = lambda row_data : bytes (json.dumps (row_data).encode())
        loads = lambda row : json.loads (row.decode())
    except Exception as e :
        print (e)
else :
    ## Use umsgpack module for row serialization
    print ("Using umsgpack module")
    try :
        import umsgpack
        import btree
        dumps = lambda row_data : umsgpack.dumps(row_data)
        loads = lambda row : umsgpack.loads(row)
    except Exception as e :
        print (e)

simpledb_available = btree is not None

class SimpleDB :
    def __init__ (self,db_file_path,key_separator = ".",dump_separator="~",auto_commit=True) :
        if btree is None :
            print ("support module(s) missing")
            #raise ???
            return
        self.db_file = None
        print (db_file_path)
        try:
            self.db_file = open(db_file_path, "r+b")
        except OSError:
            self.db_file = open(db_file_path, "w+b")
        self.db = btree.open (self.db_file)
        self.key_separator = key_separator
        self.key_low = ""
        self.key_high = "~~~~~"
        self.dump_separator = dump_separator
        self.auto_commit = auto_commit

    ## builds btree key from table_name and key
    def build_key (self,table_name,key="") -> bytes :
        pk = [table_name]
        if isinstance (key, list) :
            pk.extend (key)
        else :
            pk.append (key)
        return bytes ((self.key_separator.join (pk)).encode ())
    ## writes/rewrites table row from row_data
    def write_row (self,table_name,pk,row_data) :
        #print ("w_r:", table_name,pk)
        key = None
        if not isinstance (pk, list) :
            key = row_data [pk]
        else :
            key = []
            for _, key_id in enumerate (pk) :
                key.append (row_data [key_id])
        db_key = self.build_key(table_name, key)
        db_row = dumps(row_data)
        self.db [db_key] = db_row
        if self.auto_commit :
            self.commit ()
    ## read row from table/key, returns None if not found
    def read_row (self,table_name,key) :
        #print ("read_row:", self.build_key (table_name, key))
        try :
            #print (loads (self.db [self.build_key (table_name, key)]))
            return loads (self.db [self.build_key (table_name, key)])
        except Exception :
            return None
    ## read next table indexed row, or first row if key is not provided
    def next_row (self,table_name,key = "") :
        row_ret = None             # Not found
        start_key = self.build_key (table_name, key)
        for db_key in self.db.keys (start_key, # None) :
                                    self.build_key (table_name, self.key_high)) :
            if db_key != start_key :
                return loads (self.db [db_key])
            
        '''
        for row in rows :
            if isinstance (row, list) :
                row_key = row[0]
            else :
                row_key = row["key"]
            if row_key != key :
                row_ret = row      # This is the next row
                break
        '''
        return row_ret
    ## Return True if this key is in table_name
    def row_exists (self,table_name,key) :
        return self.build_key (table_name, key) in self.db
    ## Delete row from table
    def delete_row (self,table_name,key) :
        if self.row_exists (table_name, key) :
            del (self.db [self.build_key (table_name, key)])
            if self.auto_commit :
                self.commit ()
    ## Returns list of keys in table
    def get_table_keys (self,table_name,start_key=None,end_key=None,limit=999999) :
        key_list = []
        key_low = start_key
        key_high = end_key
        if key_low is None :
            key_low = self.key_low
        if key_high is None :
            key_high = self.key_high
        #
        for key in self.db.keys (self.build_key (table_name, key_low) ,
                                      self.build_key (table_name, key_high)) :
            key = str (key.decode())
            #print ("gtk key:", key)
            key_elements = str (key).split (self.key_separator)
            key_list.append (key_elements [1])   # table key only
            if len (key_list) >= limit :
                break
        return key_list
    ## Returns list of rows in a table
    def get_table_rows (self,table_name,start_key=None,end_key=None,limit=999999) :
        rows = []
        key_low = start_key
        key_high = end_key
        if key_low is None :
            key_low = self.key_low
        if key_high is None :
            key_high = self.key_high
        #
        for row in self.db.values (self.build_key (table_name, key_low) , # None) :
                                      self.build_key (table_name, key_high)) :
            rows.append (loads (row))   # table row
            if len (rows) >= limit :
                break
        return rows
    ## Returns list of rows in a table
    def get_table_items (self,table_name,start_key=None,end_key=None,limit=999999) :
        items = []
        key_low = start_key
        key_high = end_key
        if key_low is None :
            key_low = self.key_low
        if key_high is None :
            key_high = self.key_high
        #
        for item in self.db.items (self.build_key (table_name, key_low) , # None) :
                                      self.build_key (table_name, key_high)) :
            items.append ([str (item[0].decode()), loads (item[1])])   # table row
            if len (items) >= limit :
                break
        print ("items:", items)
        return items

    ## dump_all
    def dump_all (self, file_path = "db_dump.txt") :
        with open (file_path, "w") as dump_file :
            for key in self.db :
                row = self.db[key]
                key = str (key.decode ())
                if USE_JSON :
                    row = str (row.decode())
                else :
                    row = umsgpack.loads(row)
                    row = json.dumps (row)
                #print (f"dump: {key}{self.dump_separator}{row}")
                #print (f"{key}{self.dump_separator}{row}", file=dump_file)
                dump_file.write (key + self.dump_separator + row + "\n")
    ## load
    def load (self, file_path = "db_dump.txt") :
        print ("Loading:", file_path)
        with open (file_path, "r") as load_file :
            for line in load_file:
                key_row = (line.strip()).split (self.dump_separator)
                #print ("key_row:",key_row)
                key = bytes (key_row[0].encode ())
                if USE_JSON :
                    row = bytes (key_row[1].encode ())
                else :
                    row = json.loads (key_row[1])
                    row = dumps (row)
                print (f"load: key={key} row={row}")
                self.db [key] = row
                self.commit ()

    ## commit updates(s), if autocommit is not set
    def commit (self) :
        self.db.flush ()
    def close (self) :
        self.commit ()
        self.db.close ()
        self.db_file.close ()

# end SimpleDB  #


def main () :
    import os
    print (os.uname())
    db_file_name = "test.db"
    try :
        os.remove (db_file_name)
        print ("Removed:", db_file_name)
    except :
        pass
    my_db = SimpleDB  (db_file_name)
    if not simpledb_available :
        import sys
        print ("db failed to initialize")
        sys.exit ()

    #my_db.load ()
    #
    my_db.write_row ("customer", "customer_number" ,  {"customer_number" : "000100" ,
                                                        "name":"Curt" ,
                                                        "dob":19560606 ,
                                                        "occupation":"retired"})
    my_db.write_row ("customer", "customer_number", {"customer_number" : "000500" ,
                                            "name":"Moe" ,
                                            "dob":19200101 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "customer_number", {"customer_number" : "010000" ,
                                            "name":"Larry" ,
                                            "dob":19210202 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "customer_number", {"customer_number" : "001000" ,
                                            "name":"Curly" ,
                                            "dob":19250303 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("invoice",
                    "invoice_number" ,
                    {"invoice_number" : "090001" ,
                    "customer_number" : "001000"})
    my_db.write_row ("invoice_line",
                    ["invoice_number", "line_number"] ,
                    {"invoice_number" : "090001" ,
                    "line_number" : "0001" ,
                    "sku" : "Snake Oil" ,
                    "price" : "100.00"})
    my_db.write_row ("invoice_line",
                    ["invoice_number", "line_number"] ,
                    {"invoice_number" : "090001" ,
                    "line_number" : "0002" ,
                    "sku" : "Aspirin" ,
                    "price" : "12.00"})
    my_db.write_row ("log",
                    0 ,
                    ["20250903122010","Error","Log error"])
    my_db.write_row ("log",
                    0 ,
                    ["20250904141020","Warning", "Log warning"])
    #
    print ("good read:", my_db.read_row ("customer", "000100")) # Good key
    print ("bad read:", my_db.read_row ("customer", "000199")) # bad key
    print ("all keys:", my_db.get_table_keys ("customer"))
    print ("rows:", my_db.get_table_rows ("customer", "000500", "990000"))
    #
    my_db.get_table_items ("customer")

    row = my_db.next_row ("customer")
    while row is not None :
        print ("row:", row)
        row = my_db.next_row ("customer", row["customer_number"])
    #
    row = my_db.next_row ("log")
    while row is not None :
        print ("row:", row)
        row = my_db.next_row ("log", row[0])
    #
    row = my_db.next_row ("error_table")
    while row is not None :
        print ("row:", row)
        row = my_db.next_row ("log", row[0])
    #
    my_db.dump_all ()
    my_db.close ()

#----------------------------------------------------
if __name__ == "__main__" :
    main ()
