import json

from ..utils import raise_if_invalid_rank_token
from ..compatpatch import ClientCompatPatch


class TagsEndpointsMixin:
    """For endpoints in ``/tags/``."""

    def tag_info(self, tag):
        """
        Get tag info

        :param tag:
        :return:
        """
        endpoint = f'tags/{tag}/info/'
        res = self._call_api(endpoint)
        return res

    def tag_related(self, tag, **kwargs):
        """
        Get related tags

        :param tag:
        :return:
        """
        endpoint = f'tags/{tag}/related/'
        query = {
            'visited': json.dumps([{'id': tag, 'type': 'hashtag'}], separators=(',', ':')),
            'related_types': json.dumps(['hashtag', 'location'], separators=(',', ':'))}
        res = self._call_api(endpoint, query=query)
        return res

    def tag_search(self, text, rank_token, exclude_list=[], **kwargs):
        """
        Search tag

        :param text: Search term
        :param rank_token: Required for paging through a single feed. See examples/pagination.py
        :param exclude_list: List of numerical tag IDs to exclude
        :param kwargs:
            - **max_id**: For pagination
        :return:
        """
        raise_if_invalid_rank_token(rank_token)
        if not exclude_list:
            exclude_list = []
        query = {
            'q': text,
            'timezone_offset': self.timezone_offset,
            'count': 30,
            'exclude_list': json.dumps(exclude_list, separators=(',', ':')),
            'rank_token': rank_token,
        }
        query.update(kwargs)
        res = self._call_api('tags/search/', query=query)
        return res

    def tags_user_following(self, user_id):
        """
        Get tags a user is following

        :param user_id:
        :return:
        """
        endpoint = f'users/{user_id}/following_tags_info/'
        return self._call_api(endpoint)

    def tag_follow_suggestions(self):
        """Get suggestions for tags to follow"""
        return self._call_api('tags/suggested/')

    def tag_follow(self, tag):
        """
        Follow a tag

        :param tag:
        :return:
        """
        endpoint = f'tags/follow/{tag}/'
        return self._call_api(endpoint, params=self.authenticated_params)

    def tag_unfollow(self, tag):
        """
        Unfollow a tag

        :param tag:
        :return:
        """
        endpoint = f'tags/unfollow/{tag}/'
        return self._call_api(endpoint, params=self.authenticated_params)

    def tag_section(self, tag, tab='top', **kwargs):
        """
        Get a tag feed section

        :param tag: tag text (without '#')
        :param tab: One of 'top', 'recent', 'places'
        :kwargs:
            **extract**: return the array of media items only
            **page**: for pagination
            **next_media_ids**: array of media_id (int) for pagination
            **max_id**: for pagination
        :return:
        """
        valid_tabs = ['top', 'recent', 'places']
        if tab not in valid_tabs:
            raise ValueError(f'Invalid tab: {tab}')

        extract_media_only = kwargs.pop('extract', False)
        endpoint = f'tags/{tag}/sections/'

        params = {
            'supported_tabs': json.dumps(valid_tabs, separators=(',', ':')),
            'tab': tab,
            'include_persistent': True,
        }

        # explicitly set known paging parameters to avoid triggering server-side errors
        if kwargs.get('max_id'):
            params['max_id'] = kwargs.pop('max_id')
        if kwargs.get('page'):
            params['page'] = kwargs.pop('page')
        if kwargs.get('next_media_ids'):
            params['next_media_ids'] = json.dumps(kwargs.pop('next_media_ids'), separators=(',', ':'))
        kwargs.pop('max_id', None)
        kwargs.pop('page', None)
        kwargs.pop('next_media_ids', None)

        params.update(kwargs)
        results = self._call_api(endpoint, params=params, unsigned=True)
        extracted_medias = []
        if self.auto_patch:
            for s in results.get('sections', []):
                for m in s.get('layout_content', {}).get('medias', []):
                    if m.get('media'):
                        ClientCompatPatch.media(m['media'], drop_incompat_keys=self.drop_incompat_keys)
                        if extract_media_only:
                            extracted_medias.append(m['media'])
        if extract_media_only:
            return extracted_medias
        return results
