import logging
import time
from functools import wraps
from uuid import uuid4

from django.template.defaultfilters import slugify
from django.utils.http import urlencode
from unidecode import unidecode

logger = logging.getLogger('moviedb')


class Colors:
    """Change color in terminal."""

    RED = '\033[0;31m'
    YELLOW = '\033[33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    RESET = '\033[0m'


class GenreIDs:
    """TMDB IDs of genres."""

    ACTION = 28
    ADVENTURE = 12
    ANIMATION = 16
    COMEDY = 35
    CRIME = 80
    DOCUMENTARY = 99
    DRAMA = 18
    FAMILY = 10751
    FANTASY = 14
    HISTORY = 36
    HORROR = 27
    MUSIC = 10402
    MYSTERY = 9648
    ROMANCE = 10749
    SCIENCE_FICTION = 878
    THRILLER = 53
    TV_MOVIE = 10770
    WAR = 10752
    WESTERN = 37


GENRE_DICT = {
    'Action': GenreIDs.ACTION,
    'Adventure': GenreIDs.ADVENTURE,
    'Animation': GenreIDs.ANIMATION,
    'Comedy': GenreIDs.COMEDY,
    'Crime': GenreIDs.CRIME,
    'Drama': GenreIDs.DRAMA,
    'Family': GenreIDs.FAMILY,
    'Fantasy': GenreIDs.FANTASY,
    'History': GenreIDs.HISTORY,
    'Horror': GenreIDs.HORROR,
    'Music': GenreIDs.MUSIC,
    'Mystery': GenreIDs.MYSTERY,
    'Romance': GenreIDs.ROMANCE,
    'Science Fiction': GenreIDs.SCIENCE_FICTION,
    'Thriller': GenreIDs.THRILLER,
    'War': GenreIDs.WAR,
    'Western': GenreIDs.WESTERN,
}

# Map to convert TMDB gender of people
GENDERS = {0: '', 1: 'F', 2: 'M', 3: 'NB'}

# Map of statuses for movies
STATUS_MAP = {
    '': 0,
    'Canceled': 1,
    'Rumored': 2,
    'Planned': 3,
    'In Production': 4,
    'Post Production': 5,
    'Released': 6,
}


def unique_slugify(instance, value: str, cur_bulk_slugs: set[str] = None) -> str:
    """Generate unique slug for a model.

    Args:
        instance: the model instance for which the slug needs to be generated.
        value (str): the value from which to generate the slug.
        cur_bulk_slugs (set[str], optional): set of current slugs that are not in db yet, for bulk creation. Defaults to None.

    Returns:
        str: final slug.
    """

    if cur_bulk_slugs is None:
        cur_bulk_slugs = set()

    model = instance.__class__

    # Transliterate the non-english words into their closest ASCII equivalents
    ascii_text = unidecode(value)

    # Truncate long slugs
    slug_field = instance._meta.get_field('slug')
    max_length = slug_field.max_length
    # Offset length by 4 to add counter at the end if duplicate slug
    slug_field_value = og_slug = slugify(ascii_text)[: max_length - 4]

    # If value is empty generate uuid4
    if not slug_field_value:
        return str(uuid4())

    existing_slugs = set(model.objects.filter(slug__startswith=og_slug).exclude(pk=instance.pk).values_list('slug', flat=True))

    counter = 1
    while slug_field_value in existing_slugs or slug_field_value in cur_bulk_slugs:
        slug_field_value = f'{og_slug}-{counter}'
        counter += 1

        # If too many similar slugs generate uuid4 instead
        if counter == 1000:
            return str(uuid4())

    return slug_field_value


def runtime(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        end = time.perf_counter()

        runtime_in_secs = int(end - start)
        hours, remainder = divmod(runtime_in_secs, 3600)
        minutes, secs = divmod(remainder, 60)

        logger.info('Runtime: %s.', f'{hours:02}:{minutes:02}:{secs:02}')

        return res

    return wrapper


def get_base_query(request):
    query_params = request.GET.copy()
    base_query = {}

    if 'query' in query_params:
        base_query['query'] = query_params['query']

    base_query = urlencode(base_query)

    return base_query


def get_crew_map(crew: dict) -> dict:
    crew_map = {
        'Director': {
            'people': [],
            'alias': {'Co-Director'},
            'pluralize': True,
            'department': 'Directing',
        },
        'Writer': {
            'people': [],
            'alias': {'Screenplay', 'Co-Writer'},
            'pluralize': True,
            'department': 'Writing',
        },
        'Producer': {
            'people': [],
            'alias': {
                'Production Supervisor',
                'Production Director',
                'Co-Producer',
                'Supervising Producer',
                'Head of Production',
            },
            'pluralize': True,
            'department': 'Production',
        },
        'Executive Producer': {
            'people': [],
            'alias': {'Co-Executive Producer'},
            'pluralize': True,
            'department': 'Production',
        },
        'Cinematography': {
            'people': [],
            'alias': {'Director of Photography', 'Camera Supervisor'},
            'pluralize': False,
            'department': 'Camera',
        },
        'Composer': {
            'people': [],
            'alias': {'Original Music Composer'},
            'pluralize': True,
            'department': 'Sound',
        },
        'Editor': {
            'people': [],
            'alias': {'Co-Editor', 'Lead Editor'},
            'pluralize': True,
            'department': 'Editing',
        },
        'Animation': {
            'people': [],
            'alias': {
                'Animation Director',
                'Animation Supervisor',
                '3D Animator',
                'Key Animation',
                'Lead Animator',
                'Opening/Ending Animation',
                'Animation Technical Director',
                'Head of Animation',
                'Senior Animator',
                'Supervising Animation Director',
            },
            'pluralize': False,
            'department': 'Visual Effects',
        },
        'Production Design': {
            'people': [],
            'alias': set(),
            'pluralize': False,
            'department': 'Art',
        },
        'Sound': {
            'people': [],
            'alias': {
                'Sound Designer',
                'Sound Editor',
                'Sound Director',
                'Sound Mixer',
                'Music Editor',
                'Sound Effects Editor',
                'Production Sound Mixer',
                'Sound Engineer',
                'Sound',
                'Sound Effects',
                'Sound Effects Designer',
                'Sound Supervisor',
                'Sound Technical Supervisor',
                'Supervising Sound Editor',
            },
            'pluralize': False,
            'department': 'Sound',
        },
        'Visual Effects': {
            'people': [],
            'alias': {
                'Creature Design',
                'Shading',
                'Modeling',
                'CG Painter',
                'Visual Development',
                'Mechanical & Creature Designer',
                'VFX Artist',
                'Visual Effects Supervisor',
                'VFX Supervisor',
                'Pyrotechnic Supervisor',
                'Special Effects Supervisor',
                '3D Supervisor',
                '3D Director',
                'Color Designer',
                'Simulation & Effects Artist',
                'VFX Editor',
                '2D Artist',
                '2D Supervisor',
                '3D Artist',
                '3D Modeller',
                'CG Animator',
                'CGI Director',
                'Character Designer',
                'Character Modelling Supervisor',
                'Creature Technical Director',
                'Digital Effects Producer',
                'Lead Character Designer',
                'VFX Director of Photography',
                'VFX Lighting Artist',
                'Visual Effects Designer',
                'Visual Effects Technical Director',
                '2D Sequence Supervisor',
                'CG Artist',
                'Compositing Artist',
                'Compositing Supervisor',
                'Creature Effects Technical Director',
                'Effects Supervisor',
                'Modelling Supervisor',
                'Senior Modeller',
                'Senior Visual Effects Supervisor',
                'Smoke Artist',
                'Visual Effects Director',
                'Visual Effects Producer',
            },
            'pluralize': False,
            'department': 'Visual Effects',
        },
        'Original Writer': {
            'people': [],
            'alias': {
                'Author',
                'Novel',
                'Characters',
                'Theatre Play',
                'Original Story',
                'Musical',
                'Idea',
                'Teleplay',
                'Opera',
                'Book',
                'Comic Book',
                'Short Story',
                'Graphic Novel',
                'Original Concept',
                'Original Film Writer',
                'Original Series Creator',
            },
            'pluralize': True,
            'department': 'Writing',
        },
        'Story': {
            'people': [],
            'alias': {'Story Supervisor'},
            'pluralize': False,
            'department': 'Writing',
        },
        'Art Direction': {
            'people': [],
            'alias': {'Supervising Art Director'},
            'pluralize': False,
            'department': 'Art',
        },
        'Set Decoration': {
            'people': [],
            'alias': {'Set Supervisor'},
            'pluralize': False,
            'department': 'Art',
        },
        'Set Designer': {
            'people': [],
            'alias': {'Set Supervisor'},
            'pluralize': True,
            'department': 'Art',
        },
        'Costume Design': {
            'people': [],
            'alias': {
                'Shoe Design',
                'Co-Costume Designer',
                'Key Costumer',
                'Key Set Costumer',
                'Costume Designer',
                'Tailor',
                'Costumer',
                'Key Dresser',
                'Lead Costumer',
                'Principal Costumer',
                'Wardrobe Designer',
                'Wardrobe Master',
                'Costume Supervisor',
                'Wardrobe Supervisor',
                'Costume Set Supervisor',
            },
            'pluralize': False,
            'department': 'Costume & Make-Up',
        },
        'Makeup Artist': {
            'people': [],
            'alias': {
                'Makeup Designer',
                'Key Makeup Artist',
                'Makeup Effects Designer',
                'Prosthetic Designer',
                'Prosthetic Makeup Artist',
                'Tattoo Designer',
                'Contact Lens Designer',
                'Extras Makeup Artist',
                'Makeup & Hair',
                'Prosthetics',
                'Prosthetics Painter',
                'Prosthetics Sculptor',
                'Prosthetic Supervisor',
                'Makeup Supervisor',
                'Special Effects Makeup Artist',
            },
            'pluralize': True,
            'department': 'Costume & Make-Up',
        },
        'Hairstylist': {
            'people': [],
            'alias': {
                'Wigmaker',
                'Hair Designer',
                'Key Hair Stylist',
                'Wig Designer',
                'Hairdresser',
                'Key Hairdresser',
                'Makeup & Hair',
                'Hair Supervisor',
            },
            'pluralize': True,
            'department': 'Costume & Make-Up',
        },
        'Music': {
            'people': [],
            'alias': {
                'Additional Soundtrack',
                'Songs',
                'Music',
                'Music Director',
                'Orchestrator',
                'Music Supervisor',
                'Conductor',
                'Musician',
                'Theme Song Performance',
                'Vocals',
                'Music Producer',
                'Music Co-Supervisor',
            },
            'pluralize': False,
            'department': 'Sound',
        },
        'Camera Operator': {
            'people': [],
            'alias': {
                'Steadicam Operator',
                'Epk Camera Operator',
                'Russian Arm Operator',
                'Ultimate Arm Operator',
                '"A" Camera Operator',
                '"B" Camera Operator',
                '"C" Camera Operator',
                '"D" Camera Operator',
            },
            'pluralize': True,
            'department': 'Camera',
        },
        'Casting': {
            'people': [],
            'alias': {'Casting Director', 'Street Casting'},
            'pluralize': False,
            'department': 'Production',
        },
        'Stunts': {
            'people': [],
            'alias': {'Stunt Coordinator'},
            'pluralize': False,
            'department': 'Crew',
        },
        'Script Supervisor': {
            'people': [],
            'alias': set(),
            'pluralize': True,
            'department': 'Directing',
        },
        'Lighting': {
            'people': [],
            'alias': {
                'Lighting Technician',
                'Best Boy Electric',
                'Gaffer',
                'Rigging Gaffer',
                'Lighting Supervisor',
                'Lighting Manager',
                'Directing Lighting Artist',
                'Master Lighting Artist',
                'Lighting Artist',
                'Lighting Coordinator',
                'Lighting Production Assistant',
                'Best Boy Electrician',
                'Electrician',
                'Rigging Grip',
                'Other',
                'Chief Lighting Technician',
                'Lighting Director',
                'Rigging Supervisor',
                'Underwater Gaffer',
                'Additional Gaffer',
                'Additional Lighting Technician',
                'Assistant Chief Lighting Technician',
                'Assistant Electrician',
                'Assistant Gaffer',
                'Best Boy Lighting Technician',
                'Daily Electrics',
                'Genetator Operator',
                'Key Rigging Grip',
                'Lighting Design',
                'Lighting Programmer',
                'O.B. Lighting',
                'Standby Rigger',
            },
            'pluralize': False,
            'department': 'Lighting',
        },
        'Assistant Director': {
            'people': [],
            'alias': {
                'First Assistant Director',
                'Second Assistant Director',
                'Third Assistant Director',
            },
            'pluralize': True,
            'department': 'Directing',
        },
        'Additional Director': {
            'people': [],
            'alias': {
                'Action Director',
                'Additional Second Assistant Director',
                'Additional Third Assistant Director',
                'Field Director',
            },
            'pluralize': True,
            'department': 'Directing',
        },
        'Additional Photography': {
            'people': [],
            'alias': {
                'Underwater Camera',
                'Still Photographer',
                'Additional Camera',
                'Helicopter Camera',
                'Additional Still Photographer',
                'Aerial Camera',
                'Aerial Director of Photography',
                'Second Unit Director of Photography',
                'Underwater Director of Photography',
                'Additional Director of Photography',
                'Additional Underwater Photography',
                'Underwater Epk Photographer',
                'Underwater Stills Photographer',
            },
            'pluralize': False,
            'department': 'Camera',
        },
    }

    whole_crew = {}
    for crew_member in crew:
        whole_crew.setdefault(crew_member.department, {}).setdefault(crew_member.job, []).append(crew_member)

    for job, job_map in crew_map.items():
        department = job_map['department']
        if department not in whole_crew:
            continue

        if job in whole_crew[department]:
            for person in whole_crew[department][job]:
                if person not in job_map['people']:
                    job_map['people'].append(person)

        if job_aliases := job_map['alias'] & set(whole_crew[department]):
            for job_alias in job_aliases:
                for person in whole_crew[department][job_alias]:
                    if person not in job_map['people']:
                        job_map['people'].append(person)

    return crew_map
