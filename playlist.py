#!/usr/bin/env python
import json
import jsonschema
import sys
import io

class PlayListException(Exception):
    """Class for PlayList exception"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

# the json schema to validate input json data
INPUT_DATA_SCHEMA = {
    'type': 'object',
    'required': ['users', 'songs', 'playlists'],
    'properties': {
        'users': { 
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['id', 'name'],
                'properties': {
                    'id': {'type': 'string'},
                    'name': {'type': 'string'}
                }
            }
        },
        'songs': { 
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['id', 'artist', 'title'],
                'properties': {
                    'id': {'type': 'string'},
                    'artist': {'type': 'string'},
                    'title': {'type': 'string'},
                }
            }
        },
        'playlists': { 
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['id', 'user_id', 'song_ids'],
                'properties': {
                    'id': {'type': 'string'},
                    'user_id': {'type': 'string'},
                    'song_ids': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                }
            }
        }
    }
}

# the json schema to validate change json
CHANGE_ADD_SONG_TO_PLAYLIST_SCHEMA = {
    'type': 'object',
    'required': ['playlist_id', 'song_ids'],
    'properties': {
        'playlist_id': {'type': 'string'},
        'song_ids': {'type': 'array', 'items': {'type': 'string'}},
    }
}

CHANGE_NEW_PLAYLIST_SCHEMA = {
    'type': 'object',
    'required': ['user_id', 'song_ids'],
    'properties': {
        'user_id': {'type': 'string'},
        'song_ids': {'type': 'array', 'items': {'type': 'string'}},
    }
}

CHANGE_REMOVE_PLAYLIST_SCHEMA = {
    'type': 'object',
    'required': ['playlist_id'],
    'properties': {
        'playlist_id': {'type': 'string'}
    }
}


class PlayList(object):

    def __init__(self):
        self._users = dict()
        self._playlists = dict()
        self._songs = dict()
        self._next_playlist_id = 0

    def load_data(self, file):
        """
        Load the input data into system's state. The state could be
        in memory or persistence database
        """

        # validate json schema
        data = json.load(file)
        try:
            jsonschema.validate(instance=data, schema=INPUT_DATA_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise PlayListException(e.message)

        for user in data['users']:
            self._users[user['id']] = user

        for song in data['songs']:
            self._songs[song['id']] = song

        for playlist in data['playlists']:
            if playlist['user_id'] not in self._users:
                raise PlayListException('user_id %s not exists' % (playlist['user_id']))

            if len(playlist['song_ids']) == 0:
                raise PlayListException("at least one existing song in playlist %s" % (playlist['id']))

            for song_id in playlist['song_ids']:
                if song_id not in self._songs:
                    raise PlayListException('song_id %s not exists' % (song_id))

            self._playlists[playlist['id']] = playlist

            # record the maxnium value of playlist_id
            # the value will be used for generate new playlist id
            playlist_id_num = int(playlist['id'])
            if playlist_id_num + 1 > self._next_playlist_id:
                self._next_playlist_id = playlist_id_num + 1

    def apply_changes(self, file):
        try:
            for change in json.load(file):
                if change['type'] == 'add_song_to_playlist':
                    jsonschema.validate(instance=change, schema=CHANGE_ADD_SONG_TO_PLAYLIST_SCHEMA)
                    self._add_song_to_playlist(change)
                elif change['type'] == 'new_playlist':
                    jsonschema.validate(instance=change, schema=CHANGE_NEW_PLAYLIST_SCHEMA)
                    self._new_playlist(change)
                elif change['type'] == 'remove_playlist':
                    jsonschema.validate(instance=change, schema=CHANGE_REMOVE_PLAYLIST_SCHEMA)
                    self._remove_playlist(change)
                else:
                    raise PlayListException("change operation %s is inalid" % (change))
        except jsonschema.exceptions.ValidationError as e:
            raise PlayListException(e.message)

    def gen_output(self, file):
        out_obj = {
            'users': [],
            'songs': [],
            'playlists': []
        }

        for user_id in sorted(self._users.keys()):
            out_obj['users'].append(self._users[user_id])

        for song_id in sorted(self._songs.keys()):
            out_obj['songs'].append(self._songs[song_id])

        for playlist_id in sorted(self._playlists.keys()):
            out_obj['playlists'].append(self._playlists[playlist_id])

        file.write(unicode(json.dumps(out_obj, ensure_ascii=False, indent=4, sort_keys=True)))

    def _get_next_playlist_id(self):
        next_id = self._next_playlist_id
        self._next_playlist_id = self._next_playlist_id + 1
        return str(next_id)

    def _add_song_to_playlist(self, change):
        playlist_id = change['playlist_id']
        if playlist_id not in self._playlists:
            raise PlayListException('playlist %s not exists' % (playlist_id))

        if len(change['song_ids']) == 0:
            raise PlayListException("at least one existing song in playlist")

        for song_id in change['song_ids']:
            if song_id not in self._songs:
                raise PlayListException('song %s not exists' % (song_id))
            if song_id not in self._playlists[playlist_id]['song_ids']:
                self._playlists[playlist_id]['song_ids'].append(song_id)

    def _remove_playlist(self, change):
        if change['playlist_id'] not in self._playlists:
            raise PlayListException('playlist %s not exists' % (change['playlist_id']))

        del self._playlists[change['playlist_id']]

    def _new_playlist(self, change):
        change['id'] = self._get_next_playlist_id()
        del change['type']
        if len(change['song_ids']) == 0:
            raise PlayListException("at least one existing song in playlist")

        for song_id in change['song_ids']:
            if song_id not in self._songs:
                raise PlayListException('song %s not exists' % (song_id))
        self._playlists[change['id']] = change


def main():
    if len(sys.argv) != 4:
        print "playlist.py <input file> <change file> <output file>"
        sys.exit(1)

    try:
        data_file_name, change_file_name, out_file_name = sys.argv[1:]
        p = PlayList()
        with io.open(data_file_name, mode='r', encoding='utf-8') as data_file:
            p.load_data(data_file)

        with io.open(change_file_name, mode='r', encoding='utf-8') as change_file:
            p.apply_changes(change_file)

        with io.open(out_file_name, mode='w', encoding='utf-8') as out_file:
            p.gen_output(out_file)
    except PlayListException as e:
        print "failed to process: %s " % (e.message)
        sys.exit(1)


if __name__ == '__main__':
    # jsonschema.validate(instance={"name": 30, "price" : 34.99}, schema=schema)
    main()
