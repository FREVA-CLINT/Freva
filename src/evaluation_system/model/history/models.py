from django.db import models
from django.contrib.auth.models import User
from evaluation_system.model.plugins.models import Version, Parameter


import json




class History(models.Model):
    """
    The class belongs to a table containing all processes, which were started with analyze.
    """
    class Meta:
        """
        Set the user's permissions
        """
        permissions = (
                       ('history_submit_job', 'Can submit a job'),
                       ('history_cancel_job', 'Can cancel a job'),
                       ('browse_full_data', 'Can search all data'),
                      )

        

    class processStatus:
        """
        The allowed statuses
        finished           - the process finished and produced output files
        finished_no_output - the process finished, but no output files were created
        scheduled          - the job was send to slurm
        running            - the job is executed
        broken             - an exception occurred
        not_scheduled      - an error occurred during scheduling
        """
        finished, finished_no_output, broken, running, scheduled, not_scheduled = range(6)
        
    class Flag:
        """
        The possible flags are:
        free    - can be accessed by all
        guest   - like public and permission for guest users
        public  - the data is accessible for every registered user
        shared  - the data is can be only accessed by certain users (to be implemented)
        private - the data is private
        deleted - the data set will be hidden
        """
        public, shared, private, deleted = range(4)
        guest = 8
        free = 9
        
    STATUS_CHOICES = ((processStatus.finished, 'finished'),
                      (processStatus.finished_no_output, 'finished (no output)'),
                      (processStatus.broken, 'broken'),
                      (processStatus.running, 'running'),
                      (processStatus.scheduled, 'scheduled'),
                      (processStatus.not_scheduled, 'not scheduled'),)
    
    FLAG_CHOICES = ((Flag.public, 'public'),
                    (Flag.shared, 'shared'),
                    (Flag.private, 'private'),
                    (Flag.deleted, 'deleted'),
                    (Flag.guest, 'users and guest'),
                    (Flag.free, 'no login required'),
                   )

    #: Date and time when the process were scheduled
    timestamp       = models.DateTimeField()
    #: Name of the tool
    tool            = models.CharField(max_length=50)
    #: Version of the tool
    version         = models.CharField(max_length=20)
    #: User ID
    version_details = models.ForeignKey(Version, default=1)
    #: The configuration this can be quiet lengthy
    configuration   = models.TextField()
    #: Output file generated by SLURM 
    slurm_output    = models.TextField()
    #: User ID
    uid             = models.ForeignKey(User, to_field='username', db_column='uid')#models.CharField(max_length=20)
    #: Status (scheduled, running, finished, cancelled)
    status          = models.IntegerField(max_length=1, choices=STATUS_CHOICES)
    #: Flag (deleted, private, shared, public)
    flag            = models.IntegerField(max_length=1, choices=FLAG_CHOICES, default=Flag.public)

    
    def __init__(self, *args, **kwargs):
        """
        Creates a dictionary for projectStatus
        """
        self.status_dict = dict()
        public_props = (name for name in dir(self.processStatus) if not name.startswith('_'))
        for name in public_props:
            self.status_dict[getattr(self.processStatus,name)] = name
        
        super(History, self).__init__(*args, **kwargs)
        
    def __str__(self, compact=True):
        conf_str = ''
        
        if compact:
            conf_str = str(self.configuration)
            if len(conf_str) > 70:
                conf_str = conf_str[:67] + '...'
            version = '' 
        else:
            items = ['%15s=%s' % (k,v) for k,v in sorted(self.config_dict().items())]
            if items:
                #conf_str = '\n' + json.dumps(self.configuration, sort_keys=True, indent=2)
                conf_str = '\nConfiguration:\n%s' % '\n'.join(items)
            # if self.results:
            #     conf_str = '%s\nOutput:\n%s' % (conf_str, '\n'.join(out_files))

            version = "%s %s" % (self.version , self.version_details.internal_version_tool)
        
        return '%s) %s%s [%s] %s' % (self.pk, self.tool, version, self.timestamp, conf_str)

        
    def slurmId(self):
        id = self.slurm_output[-8:-4]

        # always return a number, even when the string is too short
        # (the default value for the string is '0')
        if not id:
            id = '0'

        return id
        

    def config_dict(self, load_default_values=False):
        """
        Converts the configuration to a dictionary
        """
        
        d = {}
        
        config = Configuration.objects.filter(history_id_id = self.id).order_by('pk')

        for c in config:
            name = c.parameter_id.parameter_name

            if load_default_values and c.is_default:
                d[name] = json.loads(c.parameter_id.default)
            else:    
                d[name] = json.loads(c.value)
            

        return d

    def status_name(self):
        """
        Returns status as string
        """    
        return self.status_dict[self.status]
    
    
    @staticmethod
    def find_similar_entries(config, max_impact=Parameter.Impact.affects_plots):
        """
        Find entries which are similar to a given configuration
        :param config: The configuration as array.
        :type config: array of history_configuration objects
        :param max_impact: The maximal impact level recognized
        :type max_impact: integer
        """

        from django.db.models import Count, Q
        
        o = Configuration.objects.all()

        length = 0

        parameter = None
        
        # We use django Q to create the query.
        # this routine builds the parameter to query.
        for c in config:
            if c.parameter_id.impact <= max_impact:
                # both parameter and value have to match
                andparam = Q(parameter_id_id=c.parameter_id) & Q(value=c.value)

                # concate all parameter pairs with an or condition
                if parameter is None:
                    parameter = andparam
                else:
                    parameter = parameter | andparam

                length += 1

        o = o.filter(parameter)

        # using a less than equal relation would allow to access matches
        # which are equal to n percent.
        o = o.values('history_id_id').annotate(hcount=Count('history_id'))

        # at the moment we return only 10 datasets
        o = o.filter(hcount=length).order_by('-id')[0:9]

        # there should be an easier method to get a list the ids of the found
        # datasets
        idlist = []

        for row in o:
            idlist.append(row['history_id_id'])

        h = History.objects.filter(pk__in=idlist)

        return h.order_by('-pk')
        

class Result(models.Model):
    """
    This class belongs to a table storing results.
    The output files of process will be recorded here.
    """

    class Filetype:
        """
        Different IDs of file types
        data      - ascii or binary data to download
        plot      - a file which can be converted to a picture
        preview   - a local preview picture (copied or converted) 
        """
        data, plot, preview = range(3)
        unknown = 9

    FILE_TYPE_CHOICES = ((Filetype.data, 'data'),
                         (Filetype.plot, 'plot'),
                         (Filetype.preview, 'preview'),
                         (Filetype.unknown, 'unknown'),)

    
    #: history id
    history_id      = models.ForeignKey(History)
    #: path to the output file
    output_file     = models.TextField()
    #: path to preview file
    preview_file    = models.TextField(default='')
    #: specification of a file type 
    file_type       = models.IntegerField(max_length=2, choices=FILE_TYPE_CHOICES)
    
    class Meta:
        """
        Set the user's permissions
        """
        permissions = (
                       ('results_view_others', 'Can view results from other users'),
                      )


    def fileExtension(self):
        """
        Returns the file extension of the result file
        """
        from os import path
        return path.splitext(self.output_file)[1]
    
    # some not yet implemented ideas
    ##: Allows a logical clustering of results
    # group           = models.IntegerField(max_length=2)
    ##: Defines an order for each group
    # group_order     = models.IntegerField(max_length=2)

class ResultTag(models.Model):
    """
    This class belongs to a table storing results.
    The output files of process will be recorded here.
    """

    class flagType:
        [caption,] = range(1)    
    
    
    TYPE_CHOICES = ((flagType.caption, 'Caption'),)
    
    #: result id
    result_id      = models.ForeignKey(Result)
    #: specification of a file type 
    type           = models.IntegerField(max_length=2, choices = TYPE_CHOICES)
    #: path to the output file
    text           = models.TextField()
    
class HistoryTag(models.Model):
    """
    This class belongs to a table storing results.
    The output files of process will be recorded here.
    """

    class tagType:
        [caption,note_public,note_private,note_deleted, follow, unfollow] = range(6)    
    
    
    TYPE_CHOICES = ((tagType.caption, 'Caption'),
                    (tagType.note_public, 'Public note'),
                    (tagType.note_private, 'Private note'),
                    (tagType.note_deleted, 'Deleted note'),
                    (tagType.follow, 'Follow'),
                    (tagType.unfollow, 'Unfollow'))
    
    #: result id
    history_id      = models.ForeignKey(History)
    #: specification of a file type 
    type            = models.IntegerField(max_length=2, choices = TYPE_CHOICES)
    #: path to the output file
    text            = models.TextField()
    #: the user, who tagged the history entry
    uid             = models.ForeignKey(User, to_field='username', db_column='uid', null=True, default=None)
    
class Configuration(models.Model):
    """
    Holds the configuration
    """
    #: history id
    history_id = models.ForeignKey(History, related_name='history_id')
    
    #: parameter number
    parameter_id = models.ForeignKey(Parameter, related_name='parameter_id')
    
    #: md5 checksum of value (not used, yet)
    md5 = models.CharField(max_length=32, default='')
    
    #: value
    value = models.TextField(null=True, blank=True)
    
    #; is the default value used?
    is_default = models.BooleanField()

