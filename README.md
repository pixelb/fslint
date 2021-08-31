# FSlint
Linux file system lint checker/cleaner with database support to reduce time and operations if you need to scan twice the same files in the folders or subfolders.

Each hashing algorithm saves the hash values of the files that it calculates on a specific database. In addition to the hash value, it saves the file creation and last modification time. If one of these two parameters changed from the last execution of FSlint, the hashing algorithm re-calculates the hash value otherwise it considers the existing hash value of the file as valid.

To accomplish it, the fslint/supprt/database file has been created and the fslint/findup file has been modified to pass the information to the database script and reduce the execution time for the hashing calculation. Moreover, with the database support, the find duplication file process can be stopped and re-started avoiding to re-calculate the hash from the beginning.
  
The usage of the command line or GUI has not been modified, so you can use the FSlint as normal. 