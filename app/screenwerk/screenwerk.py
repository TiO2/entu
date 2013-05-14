import logging
import json
import magic
from datetime import datetime
from croniter import croniter

from main.helper import *
from main.db import *


class Schedule():
    days = 3
    def get_schedule(self, entity_id):
        now = datetime.datetime.now()
        last_day = now + datetime.timedelta(days=self.days)
        schedule_dict = {}

        # get screen
        screen = self.get_entities(entity_id=entity_id, limit=1, only_public=True)
        if not screen:
            return {}

        # get group
        group_id = screen.get('properties', {}).get('screen-group', {}).get('values', [{}])[0].get('db_value')
        if not group_id:
            return {}
        group = self.get_entities(entity_id=group_id, limit=1, only_public=True)
        if not group:
            return {}

        # get configuration
        configuration_id = group.get('properties', {}).get('configuration', {}).get('values', [{}])[0].get('db_value')
        if not configuration_id:
            return {}
        configuration = self.get_entities(entity_id=configuration_id, limit=1, only_public=True)
        if not configuration:
            return {}

        # get schedules
        schedule_ids = self.get_relatives(ids_only=True, entity_id=configuration_id, relationship_definition_keyname='child', entity_definition_keyname='sw-schedule', only_public=True)
        if not schedule_ids:
            return {}
        schedules = self.get_entities(entity_id=schedule_ids, only_public=True)
        if not schedules:
            return {}

        for s in schedules:
            # get schedule valid-from date
            valid_from = s.get('properties', {}).get('valid-from', {}).get('values', [{}])[0].get('db_value')
            if valid_from and valid_from > last_day:
                continue
            if not valid_from or valid_from < now:
                valid_from = now
            valid_from = valid_from - datetime.timedelta(seconds=1)

            # get schedule valid-to date
            valid_to = s.get('properties', {}).get('valid-to', {}).get('values', [{}])[0].get('db_value')
            if valid_to and valid_to < now:
                continue
            if not valid_to or valid_to > last_day:
                valid_to = last_day
            valid_to = valid_to + datetime.timedelta(seconds=1)

            # get run times
            run_times = []
            for crontab in s.get('properties', {}).get('crontab', {}).get('values', []):
                if not crontab.get('value'):
                    continue

                try:
                    crontab_iter = croniter(crontab.get('value'), valid_from)
                except:
                    continue

                if valid_from < now:
                    run_time = crontab_iter.get_prev(datetime.datetime)
                else:
                    run_time = crontab_iter.get_next(datetime.datetime)

                while run_time <= valid_to:
                    run_times.append(run_time)
                    run_time = crontab_iter.get_next(datetime.datetime)
            if not run_times:
                continue
            run_times = sorted(list(set(run_times)))

            # get layout
            layout_id = s.get('properties', {}).get('layout', {}).get('values', [{}])[0].get('db_value')
            if not layout_id:
                self.write('No layout id!')
                continue
            layout = self.get_entities(entity_id=layout_id, limit=1, only_public=True)
            if not layout:
                continue

            # get layout-playlists
            layout_playlist_ids = self.get_relatives(ids_only=True, entity_id=layout_id, relationship_definition_keyname='child', entity_definition_keyname='sw-layout-playlist', only_public=True)
            if not layout_playlist_ids:
                continue
            layout_playlists = self.get_entities(entity_id=layout_playlist_ids, only_public=True)
            if not layout_playlists:
                continue

            for lp in layout_playlists:
                # get playlist
                playlist_id = lp.get('properties', {}).get('playlist', {}).get('values', [{}])[0].get('db_value')
                if not playlist_id:
                    continue
                playlist = self.get_entities(entity_id=playlist_id, limit=1, only_public=True)
                if not playlist:
                    continue

                # get playlist-media
                playlist_media_ids = self.get_relatives(ids_only=True, entity_id=playlist_id, relationship_definition_keyname='child', entity_definition_keyname='sw-playlist-media', only_public=True)
                if not playlist_media_ids:
                    continue
                playlist_medias = self.get_entities(entity_id=playlist_media_ids, only_public=True)
                if not playlist_medias:
                    continue

                for pm in playlist_medias:
                    # get media
                    media_id = pm.get('properties', {}).get('media', {}).get('values', [{}])[0].get('db_value')
                    if not media_id:
                        continue
                    media = self.get_entities(entity_id=media_id, limit=1, only_public=True)
                    if not media:
                        continue
                    if not media.get('properties', {}).get('type', {}).get('values', [{}])[0].get('value'):
                        continue

                    media_file = '%s://%s/screenwerk/file-%s' % (self.request.protocol, self.request.host, media.get('properties', {}).get('file', {}).get('values', [{}])[0].get('db_value')) if media.get('properties', {}).get('file', {}).get('values', [{}])[0].get('db_value', '') else media.get('properties', {}).get('url', {}).get('values', [{}])[0].get('value')
                    media_type = media.get('properties', {}).get('type', {}).get('values', [{}])[0].get('value', '').lower()
                    media_ratio = media.get('properties', {}).get('width', {}).get('values', [{}])[0].get('value', 1) / media.get('properties', {}).get('height', {}).get('values', [{}])[0].get('value', 1)
                    if media_type == 'video':
                        pass

                    if not media.get('properties', {}).get('url', {}).get('values', [{}])[0].get('value') and not media.get('properties', {}).get('file', {}).get('values', [{}])[0].get('db_value'):
                        continue

                    for t in run_times:
                        if playlist.get('properties', {}).get('valid-from', {}).get('values', [{}])[0].get('db_value', now) > t:
                            continue
                        if playlist.get('properties', {}).get('valid-to', {}).get('values', [{}])[0].get('db_value', last_day) < t:
                            continue
                        if pm.get('properties', {}).get('valid-from', {}).get('values', [{}])[0].get('db_value', now) > t:
                            continue
                        if pm.get('properties', {}).get('valid-to', {}).get('values', [{}])[0].get('db_value', last_day) < t:
                            continue
                        if media.get('properties', {}).get('valid-from', {}).get('values', [{}])[0].get('db_value', now) > t:
                            continue
                        if media.get('properties', {}).get('valid-to', {}).get('values', [{}])[0].get('db_value', last_day) < t:
                            continue

                        # schedule
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {})['start'] = int(time.mktime(t.timetuple()))
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {})['cleanup'] = bool(s.get('properties', {}).get('cleanup', {}).get('values', [{}])[0].get('db_value', False))
                        # playlist
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['id'] = lp.get('id')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['top'] = lp.get('properties', {}).get('top', {}).get('values', [{}])[0].get('value', 0)
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['left'] = lp.get('properties', {}).get('left', {}).get('values', [{}])[0].get('value', 0)
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['width'] = lp.get('properties', {}).get('width', {}).get('values', [{}])[0].get('value', 100)
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['height'] = lp.get('properties', {}).get('height', {}).get('values', [{}])[0].get('value', 100)
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['zindex'] = lp.get('properties', {}).get('zindex', {}).get('values', [{}])[0].get('value', 1)
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {})['loop'] = bool(lp.get('properties', {}).get('loop', {}).get('values', [{}])[0].get('db_value', False))
                        # media
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['id'] = pm.get('id')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['top'] = pm.get('properties', {}).get('top', {}).get('values', [{}])[0].get('value')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['left'] = pm.get('properties', {}).get('left', {}).get('values', [{}])[0].get('value')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['width'] = pm.get('properties', {}).get('width', {}).get('values', [{}])[0].get('value')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['height'] = pm.get('properties', {}).get('height', {}).get('values', [{}])[0].get('value')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['duration'] = pm.get('properties', {}).get('duration', {}).get('values', [{}])[0].get('value')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['ordinal'] = pm.get('properties', {}).get('ordinal', {}).get('values', [{}])[0].get('value')
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['type'] = media_type
                        schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['src'] = media_file
                        if media_type == 'video':
                            schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['ratio'] = media_ratio
                            schedule_dict.setdefault(int(time.mktime(t.timetuple())), {}).setdefault('playlists', {}).setdefault(lp.get('id'), {}).setdefault('media', {}).setdefault(pm.get('id'), {})['mute'] = bool(pm.get('properties', {}).get('mute', {}).get('values', [{}])[0].get('db_value', 0))

            delete_keys_from_dict(schedule_dict)

            return schedule_dict


class ShowPlayer(myRequestHandler, Entity, Schedule):
    def get(self, entity_id):
        screen = self.get_entities(entity_id=entity_id, limit=1, only_public=True)
        if not screen:
            return self.missing()

        schedule = self.get_schedule(entity_id=entity_id)
        for s in schedule.keys():
            for p in schedule[s]['playlists'].keys():
                schedule.setdefault(s, {}).setdefault('playlists', {}).setdefault(p, {})['media'] = schedule.get(s, {}).get('playlists', {}).get(p, {}).get('media', {}).values()
            schedule.setdefault(s, {})['playlists'] = schedule.get(s, {}).get('playlists', {}).values()
        schedule = {'schedules': schedule.values() }

        self.render('screenwerk/template/index.html',
            screen = screen,
            schedule = json.dumps(schedule),
        )



class ShowOfflineManifest(myRequestHandler, Entity, Schedule):
    def get(self, entity_id):
        schedule = self.get_schedule(entity_id=entity_id)
        files = []
        for s in schedule.values():
            for p in s.get('playlists', {}).values():
                for m in p.get('media', {}).values():
                    files.append(m.get('src'))
        files = sorted(list(set(files)))

        self.render('screenwerk/template/cache.manifest',
            files = files
        )


class ShowSchedule(myRequestHandler, Entity, Schedule):
    def get(self, entity_id):
        schedule = self.get_schedule(entity_id=entity_id)

        for s in schedule.keys():
            for p in schedule[s]['playlists'].keys():
                schedule.setdefault(s, {}).setdefault('playlists', {}).setdefault(p, {})['media'] = schedule.get(s, {}).get('playlists', {}).get(p, {}).get('media', {}).values()
            schedule.setdefault(s, {})['playlists'] = schedule.get(s, {}).get('playlists', {}).values()
        schedule = {'schedules': schedule.values() }

        self.write(schedule)


class ShowFile(myRequestHandler, Entity):
    def get(self, file_id):
        files = self.get_file(file_id)
        if not files:
            return self.missing()

        file = files[0]
        ms = magic.open(magic.MAGIC_MIME)
        ms.load()
        mime = ms.buffer(file.file)
        ms.close()

        self.add_header('Content-Type', mime)
        self.add_header('Content-Disposition', 'inline; filename="%s"' % file.filename)
        self.write(file.file)


def delete_keys_from_dict(dict_del):
    for k in dict_del.keys():
        if isinstance(dict_del[k], dict):
            delete_keys_from_dict(dict_del[k])
        if dict_del[k] == None:
            del dict_del[k]
    return dict_del


handlers = [
    (r'/screenwerk/screen-(.*)/schedule', ShowSchedule),
    (r'/screenwerk/screen-(.*)/cache.manifest', ShowOfflineManifest),
    (r'/screenwerk/screen-(.*)', ShowPlayer),
    (r'/screenwerk/file-(.*)', ShowFile),
]
