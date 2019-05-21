#!/usr/bin/env python
import unittest
from playlist import PlayList, PlayListException
from cStringIO import StringIO
import json

INPUT = """
    {
      "users" : [
        {
          "id" : "1",
          "name" : "Albin Jaye"
        }
      ],
      "playlists" : [
        {
          "id" : "1",
          "user_id" : "1",
          "song_ids" : [
            "1",
            "2"
          ]
        },
        {
          "id" : "2",
          "user_id" : "1",
          "song_ids" : [
            "1"
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
"""

CHANGE = """
    [
        {
            "type": "add_song_to_playlist",
            "playlist_id": "2",
            "song_ids" : ["2"]
        },
        {
            "type": "new_playlist",
            "user_id": "1",
            "song_ids": ["1", "2"]
        },
        {
            "type": "remove_playlist",
            "playlist_id": "1"
        }
    ]
"""

class TestPlaylist(unittest.TestCase):

    def test_normal_case(self):
        p = PlayList()

        p.load_data(StringIO(INPUT))
        p.apply_changes(StringIO(CHANGE))
        output = StringIO()
        p.gen_output(output)
        obj = json.loads(output.getvalue())
        self.assertEqual(len(obj['users']), 1)
        self.assertEqual(obj['users'][0]['id'], '1')
        self.assertEqual(len(obj['playlist']), 2)
        self.assertEqual(obj['playlist'][0]['id'], '2')
        self.assertEqual(obj['playlist'][0]['song_ids'], ['1', '2'])
        self.assertEqual(obj['playlist'][1]['id'], '3')
        self.assertEqual(obj['playlist'][1]['song_ids'], ['1', '2'])

    def test_input_valiate(self):
        p = PlayList()

        ## playlist's user_id is invalid
        input = """
            {
              "users" : [{"id" : "1", "name" : "Albin Jaye"} ],
              "playlists" : [{"id" : "1", "user_id" : "2", "song_ids" : ["1"] } ],
              "songs": [{"id" : "1", "artist": "Camila Cabello", "title": "Never Be the Same"}
              ]
            }
        """
        with self.assertRaises(PlayListException):
            p.load_data(StringIO(input))

        # playlist's song_id is invalid
        input = """
            {
              "users" : [{"id" : "1", "name" : "Albin Jaye"} ],
              "playlists" : [{"id" : "1", "user_id" : "1", "song_ids" : ["2"] } ],
              "songs": [{"id" : "1", "artist": "Camila Cabello", "title": "Never Be the Same"}
              ]
            }
        """
        with self.assertRaises(PlayListException):
            p.load_data(StringIO(input))

    def test_change_input(self):
        p = PlayList()
        p.load_data(StringIO(INPUT))

        # below schema in change:
        # 1. option type is not valid
        # 2. miss filed 'song_ids'
        change = """
            [
                {
                    "type": "invalid_option"
                }
            ]
        """
        with self.assertRaises(PlayListException):
            p.apply_changes(StringIO(change))

        change = """
            [
                {
                    "type": "add_song_to_playlist",
                    "playlist_id": "2"
                }
            ]
        """
        with self.assertRaises(PlayListException):
            p.apply_changes(StringIO(change))

    def test_operate_on_not_exists_playlist(self):
        change = """
            [
                {
                    "type": "remove_playlist",
                    "playlist_id": "10"
                }
            ]
        """
        p = PlayList()
        p.load_data(StringIO(INPUT))
        with self.assertRaises(PlayListException):
            p.apply_changes(StringIO(change))

        change = """
            [
                {
                    "type": "add_song_to_playlist",
                    "playlist_id": "100",
                    "song_ids" : ["2"]
                }
            ]
        """
        p = PlayList()
        p.load_data(StringIO(INPUT))
        with self.assertRaises(PlayListException):
            p.apply_changes(StringIO(change))

    def test_operate_on_not_exists_song(self):
        change = """
            [
                {
                    "type": "add_song_to_playlist",
                    "playlist_id": "1",
                    "song_ids" : ["100"]
                }
            ]
        """
        p = PlayList()
        p.load_data(StringIO(INPUT))
        with self.assertRaises(PlayListException):
            p.apply_changes(StringIO(change))


    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()
