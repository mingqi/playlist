# How to install
## install with Docker
I recommend you install software by Docker. It's will be very easy. Run below command to download image to your computer:

```
docker pull shaomq/playlist
```

## install without Docker

1. first install Python 2.7 on your machine

2. clone code to a separate directory

```
git clone https://github.com/mingqi/playlist.git
```

3. install python dependencies

```
cd playlist
pip install -r requirements.txt
```

# How to use
## use it with Docker
```
docker run -it shaomq/playlist /playlist/playlist.py <input file> <change file> <output file>
```

here:
* input file: the path of input files that have all data. File is json format
* change file: the path of change file. File is json format.
* output file: the path of out file. File is json format.

## use it without Docker

```
cd playlist
./playlist.py <input file> <change file> <output file>
```

## the change file's format
Below is a example:
```
[
    {
        "type": "add_song_to_playlist",
        "playlist_id": "2",
        "song_ids" : ["21","22"]
    },
    {
        "type": "new_playlist",
        "user_id": "1",
        "song_ids": ["1", "2", "3"]
    },
    {
        "type": "remove_playlist",
        "playlist_id": "3"
    }
]
```

# How to scale his application to handle very large input files
I think that below changes can be made to scale the application:
1. Process the file in a streaming manner
2. Persistence data in the local file system, distributed file system or distributed database 
3.  Use a job scheduling system to parallelly compute.

## 1. Process the file in a streaming manner
currently, files (input, change and output files) be processed by reading the entire JSON file into memory. It's very easy to cause out of memory and requires the same amount of memory as file size.  Use streaming parser will fix the issue. 

### JSON streaming process is complex and difficult to use
I did research on JSON streaming.  There are many open source projects work on this for every language. But all of them look likes complex and not convinces to use, especially to generate the JSON file.  I also suspect the performance.  The JSON format is hierarchical. It's native difficult to process in a streaming manner. 

### Use CSV format 
I can using the CSV format file. That's will be very easy to write a streaming parser with few lines codes. The original JSON and CSV format look like:

```
{
  "users" : [
    {
      "id" : "1",
      "name" : "Albin Jaye"
    },
    {
      "id" : "2",
      "name" : "Dipika Crescentia"
    }
  ],
  "playlists" : [
    {
      "id" : "1",
      "user_id" : "2",
      "song_ids" : [
        "1",
        "2"
      ]
    }
  ],
  "songs": [
    {
      "id" : "1",
      "artist": "Camila Cabello",
      "title": "Never Be the Same"
    },
    {
      "id" : "2",
      "artist": "Zedd",
      "title": "The Middle"
    }
  ]
}

```


Corresponding CVS format is:
```
user, 1, Albin Jaye
user, 2, Dipika Crescentia
song, 1, Camila Cabello, Never Be the Same
song, 2, Zedd, The Middle
playlists, 1, 2, 1, 2
```

## 2. Persistence data in the local file system, distributed file system or distributed database 

Persistence data in the local file system can break through the limitation of memory size. Persistence data in the distributed database or distributed file system can break through the limitation of a single machine.

## 3. Use a job scheduling system to parallelly compute.
We can use some job scheduling systems to coordinate many machines and processes to do the job parallelly.  For example, can use Hadoop's map reduce job scheduling. 

For example, if we can 10 million playlist data need to load, we can split them to 10 or more jobs to do that parallelly. That will hugely speed up the process. 

But be careful the process order of different types of jobs.  The playlist should be processed only if the user and song data done.  
