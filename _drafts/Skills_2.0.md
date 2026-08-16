# video 1
En este video



Capítulos

Transcripción
Buscar en el video
Intro
0:00
Claude just dropped Skills 2.0 and it's
0:02
a gamecher for anyone working with Cloud
0:04
Co-work or Cloud Code. With Skills 2.0,
0:06
we now have built-in evals or testing
0:08
which allows anyone to build more
0:10
reliable, better performing skills and
0:11
automations way faster. So, in this
0:13
video, I'll show you why Skills 2.0 are
0:15
a big deal and how they work. And I'll
0:17
show you exactly how to use them to
0:19
build better skills fast with plenty of
0:21
examples. Now, I'll show you a demo of
Example of Skills 2.0
0:23
Skills 2.0 in cloth co-work, but it will
0:25
work very similar in cloth code if you
0:26
use that. So, what are these skills 2.0?
0:29
Basically, Enthropic just updated their
0:31
skill creator skill. You can see that it
0:33
now has folders with Eval viewer agents
0:36
that can analyze, compare, and grade and
0:39
scripts for benchmarking and report.
0:41
Now, you don't have to understand what's
0:43
actually in there, but this basically
0:44
allows us to run automatic tests on our
0:47
skills in order to improve them faster.
0:49
For example, here I ran a test on my
0:51
YouTube to newsletter repurposing skill.
0:53
It ran five test variations and
0:56
automatically scored performance based
0:58
on my criteria like word count, m dashes
1:01
and if it included personal stories and
1:03
then automatically scored the
1:05
performance of each of the test. I can
1:07
also check the outputs from the test or
1:08
the eval here in this report and based
1:11
on the performance results and my
1:13
feedback which I can give here for all
1:15
the different variations, it can
1:17
optimize a skill far faster and
1:19
drastically improve the way we build
1:20
good skills. Now although this is a
What Are Skills?
1:22
great feature, it is actually really
1:24
important to understand how to use this
1:26
efficiently. Now before showing you a
1:27
full demo of how to use them and all the
1:29
use cases for them, it's important to
1:30
understand how they actually work and
1:32
what kind of testing we can do. Now if
1:34
you're still unfamiliar with skills,
1:35
skills is basically a way we can
1:36
automate any task or workflow by simply
1:38
prompting clot code or clot co-work. It
1:41
basically includes a skill MD, which is
1:43
just a text file that instructs clot
1:45
what process to follow. It can also have
1:47
additional information or context in a
1:49
text format, a non-ext format, and can
1:52
even include code. And this is extremely
1:54
powerful because, for example, me and my
1:55
team are building out skills and
1:57
automations for all our daily tasks
1:59
across all our business departments. So,
2:00
we have skills for sales, marketing,
2:03
operations, etc. If you want to use or
2:05
customize some of our skills, you can
2:07
also check out my AI community in the
2:08
link in the description below where we
2:10
list them all out. also have one-on-one
2:11
unlimited tech help available and weekly
2:13
AI workshops where we dive a lot deeper
2:15
into these tools. Now, I recently did a
2:17
full tutorial on how to build skills,
2:19
which I highly recommend you check out
2:20
if this is still new to you. I'll make
2:22
sure to put in the link in the
2:23
description below, too. Now, why are
2:24
these evals or built-in testing features
How Skills 2.0 Work
2:26
such a big deal? Now, the main reason is
2:28
because skills are really never
2:29
finished, right? Rarely do you have a
2:31
perfectly optimized skill at the first
2:33
try? In fact, just like with software or
2:36
any other type of engineering, iterating
2:38
on skills after you've built a first
2:40
version is actually the most important
2:42
step to get to good skills. Most of my
2:44
skills I had to iterate on multiple
2:46
times, sometimes five to 10 times before
2:48
they became functional and optimal. But
2:50
before this new feature, it was hard to
2:52
know what to adapt or what to iterate on
2:54
to get a better output from your skill.
2:56
And this is what the new skill update
2:58
makes 10 times uh easier and more
3:00
efficient. Now, before showing you some
3:02
examples of how to do this efficiently,
3:04
how do they actually work? Now, as I
3:06
showed, they've basically just updated
3:07
the existing skill creator skill to now
3:10
include these evals, which basically
3:12
just means testing. So, if you've
3:14
already created a skill, you know, you
3:15
can just build a skill by prompting it.
3:17
And this will still work the same way
3:18
with these new skills. But now, after
3:21
you've created a skill, Cloud will
3:22
automatically ask you to test your
3:24
skill. But instead of just running one
3:26
test and you evaluating the output, it
3:28
can run multiple tests at the same time
3:30
and focus on testing specific things and
3:32
give benchmarks or scores for them. For
3:34
example, you can test on speed, token
3:37
usage, output quality, uh tool call use,
3:40
let's say copyrightiting style, but
3:42
really anything you want to test it on.
3:44
It will then give you that data in a
3:45
nice structured document that I showed
3:47
you for you to analyze. And based on the
3:49
results, both good and bad, and your
3:51
feedback, it can easily update and
3:52
optimize the skill very fast. If you do
3:55
a few of these iteration loops, you can
3:56
get to really good skills really fast.
3:58
Now, besides this, there's another new
4:00
thing we can do that can help you
4:01
optimize the skills you build even more,
4:03
which is through AB tests. And in AB
4:06
tests, you're basically testing
4:08
different versions of skills to see
4:10
which one works best. You could also
4:12
test your current skill against
4:14
non-sklls to see if it actually performs
4:16
better than if you wouldn't have a skill
4:18
at all. But Entropic mostly recommends
4:20
to do this when a new model is released
4:22
like let's say for example Opus 4.7 or
4:25
8. Um because your skill might become
4:27
irrelevant when models become more
4:29
powerful. So let me show you some
Building a Skill from Scratch
4:30
examples of how to create these skills,
4:32
test them efficiently with both evals
4:35
and AB test to get to good skills fast.
4:37
I'll just show you a full process of
4:39
building and testing a skill to get to
4:41
good skills fast. Now, here you can see
4:42
that I built my YouTube to newsletter
4:44
repurposing skill from scratch. And I
4:46
did this using a prompt format that I
4:48
covered in my last video on skill
4:50
building to get to a good first version
4:52
of the skill. Now, this is not hard
4:54
science, but it's a good framework uh to
4:56
go through to make sure you include all
4:58
best practices when creating a new
5:00
skill. Now, if you want a breakdown of
5:02
the entire framework, you can you can
5:03
also check out my last video, but I'll
5:04
go through it very quickly here, too.
5:06
Now, even though we can prompt it really
5:08
quick to create a skill, actually
5:09
thinking about it and putting some
5:10
effort in is really important because
5:12
the more accurate and precise you are uh
5:14
both when creating a skill and testing
5:16
the skill um the more efficient this
5:18
process and the better your skill is
5:19
going to be. So, in this case, I'd said
5:21
create a skill according to the
5:23
following guidelines. Then I gave it a
5:24
description of what the name of the
5:26
skill uh should be and how uh the skill
5:28
should be triggered. So, in this case,
5:30
the name of the skill should be YouTube
5:31
to newsletter. It should be triggered
5:32
anytime a user mentions that he wants to
5:34
repurpose a YouTube video into a
5:36
newsletter. Then I gave it the main goal
5:38
for the skill. In this case, a skill
5:39
that repurposes a YouTube video into a
5:41
full ready to publish newsletter issue
5:43
within written in my voice and style.
5:45
Then I covered the connectors that it
5:47
has to use in this skill. In this skill,
5:48
you need to use the YouTube transcript
5:50
MCP from ampify to extract the video
5:53
transcript. Also, I specified the
5:55
reference files it has to include in the
5:56
skill. In this case, these are the
5:58
reference files uh that I find get my
6:00
copywriting skills to way better
6:02
outputs. Like for example, the what we
6:04
do, which is basically a description of
6:06
my business, my ICP, my voice
6:08
personality, a newsletter strategy doc,
6:11
a writing framework, and newsletter
6:13
examples, which is one of the most
6:15
important for copywriting skills. So
6:17
these skills actually follow your tone
6:19
of voice. And then I laid out the entire
6:21
process it has to follow to get to that
6:23
final outcome. So in this case, ask the
6:25
user for the YouTube video they want to
6:27
repurpose, extract the video transcript
6:30
using ampify, then read the reference
6:32
files, analyze the transcript, and
6:34
suggest five newsletter angles. In this
6:37
process, I also define where I want to
6:39
have human in the loop. For example,
6:41
here present the suggestions using the
6:42
QA box and where I want the output to
6:45
be. In this case, save the newsletter as
6:47
a word document. And lastly, one section
6:50
I like to include in the skill prompts
6:52
is the progressive updates. Whenever a
6:54
user specifies specifically not to do
6:56
something anymore, it should
6:57
automatically update the role section in
6:59
the skill MD. And this is basically how
7:01
your skill can become self-learning
7:03
because anytime you can give it quick
7:04
feedback, it can automatically update
7:06
the skill. So it won't do that next
7:08
time. Now with this prompt and these
7:10
reference files, it started creating the
7:11
skill as you can see here. Now of course
How to Use Tests & Evals
7:13
this was already possible before the
7:14
update of the skills, but now you see
7:16
Claude asked me uh want me to run some
7:18
test cases to make sure it performs well
7:20
or are you happy to try it out directly?
7:22
So in this case I said yes okay please
7:24
run some tests and now it started doing
7:26
an eval. So you can see it says let me
7:28
set up uh test use cases and run them.
7:30
I'll create three realistic test bronze
7:32
with different YouTube videos. It then
7:34
basically spins up three different sub
7:36
aents to run these tests in parallel.
7:38
And then it started evaluating the
7:39
outputs based on uh the criteria as you
7:42
can see here. Now this is the point why
7:44
we need to actually understand how to
7:45
use this efficiently because in this
7:47
case I didn't specify what the testing
7:49
criteria uh should be or what to
7:51
optimize for. So cloud basically came up
7:53
with the criteria itself probably with
7:55
some information from my reference file.
7:57
But in this case, it defined these
7:58
criterias, right? A PS section with a
8:00
soft pitch to the to my AI community, a
8:03
signature sign off with Ben, a word
8:06
count range, and if it actually produced
8:09
a docs file. Now, and of course, this
8:11
can be useful to sort of test if your
8:12
skill actually is functioning or or
8:14
working. But if you actually want to
8:15
optimize it, we want to be much more
8:17
precise on what to optimize for and the
8:20
criteria to test on. And I'll show you
8:22
an example of that in a second. But as a
8:24
result here we get uh of course that
8:26
report where we can basically see uh the
8:28
full execution of each of the tests. Uh
8:30
so we can see the prompt here that was
8:32
used in this specific test the steps
8:35
that were completed. So in this case
8:36
video collection transcript extraction
8:39
reference file analysis. So basically
8:41
checked if it actually followed the
8:43
step-by-step process instructed in the
8:45
skill. Now in this case it did it well.
8:46
And then it also gives us the full
8:48
output of the newsletter. We can also
8:51
see the formal grades of the criteria it
8:53
tests for here. In this case, zero
8:55
failed. And we can give feedback on each
8:57
of the specific test results here. And
9:00
if we click on next here, we can go
9:02
through all the different variations of
9:03
test tests and give feedback. And if we
9:06
want to optimize the skill, we can
9:07
basically just tell Claude to either do
9:09
it based on the results of the test he
9:11
run or combine it with together with our
9:13
feedback. So if you add feedback to each
9:15
of the tests, you can just click copy
9:17
here and add that then to the chat. and
9:20
it will have uh more context on how to
Tests & Evals Best Practices
9:22
optimize this. Now again giving a basic
9:24
prompt like I did like saying uh run
9:26
some tests may be useful again to check
9:29
if if it's actually functional but if
9:31
you actually want to optimize it uh for
9:32
specific criteria we have to be much
9:34
more specific. So what I recommend you
9:36
at least include when you prompt clot to
9:38
run an EVA or a test is to um define
9:41
what you're going to optimize this test
9:43
for. And it's really important to choose
9:44
one here. Don't try to optimize five or
9:47
six different things at the same times
9:48
because there there will be too many
9:49
variables. So you want to test one thing
9:51
at a time. Optimize one thing at a time.
9:53
And also you want to define the criteria
9:55
for the evals. And optionally you can
9:57
define how the test should be done. So
9:59
for example in my case I said let's run
10:01
a new test and we're going to optimize
10:03
the test for matching Ben's
10:04
copyrightiting style and voice as
10:06
closely as possible. Don't use the
10:08
current test. It should be a new new
10:10
test. Now the criteria for the evals are
10:12
how clo closely does it follow Ben's
10:14
example references second does it have m
10:17
dashes third the length of the
10:20
newsletter and fourth does it include
10:22
personal stories or references from
10:24
Ben's personal background reference file
10:26
and then I defined how the test should
10:28
be done because of course I don't want
10:29
this to run on five different YouTube
10:31
videos I want to see different outputs
10:33
based on the same YouTube video so we're
10:35
going to use only one YouTube video to
10:36
test five different variations and you
10:38
can also define how many tests
10:40
variations you want the eval or the test
10:42
to run. So in this case I specified
10:44
five. Then it ran the test again and in
10:47
this case it ran the test based on my
10:49
criteria. So it ran it on a style match
10:52
and you can see two out of five failed
10:54
word count and personal stories and you
10:56
can see one out of five failed. You can
10:58
see this is already a much more useful
11:00
test result. And based on these test
11:02
results and evals, I can tell Claude to
11:05
optimize for um not failing on the
11:07
personal stories on the style match and
11:09
it will already do a pretty good job in
11:11
optimizing my skill. But of course again
11:13
I can go into the review and give it
11:16
extra feedback. Just copy it, add it
11:18
here and it can update the skill to make
11:19
a better version.
How to Use A/B tests
11:21
Now lastly, let me show you a quick
11:23
example of how and when to use AB tests
11:26
where we actually test different
11:27
versions of skills against each other.
11:29
Now this is generally what you want to
11:31
do only when you already have a
11:33
functioning and sort of good performing
11:35
skill. And these AB tests basically
11:37
allow you to optimize functions of
11:39
skills even more. Now the way we do it
11:41
is by just telling Claude to run an AB
11:43
test on the skill. For example, here I
11:45
said use the creator skill to run an AB
11:47
test on the YouTube to newsletter skill
11:49
so that we optimize the skill for speed.
11:51
It can't affect the step-by-step
11:53
process. The process still has to be
11:54
there and the reference file still has
11:56
to be read. It has to use u this YouTube
11:58
link for the test. Now, of course, you
12:00
can use these AB tests to optimize for
12:02
speed, token usage, output quality,
12:04
again, really anything you can imagine,
12:06
but in my opinion is much more focused
12:08
on really trying to get from a already
12:10
good skill to a great skill or a more
12:12
efficient skill. What it does in this
12:14
case is it basically spins up a sec
12:16
second skill, a version B that in this
12:18
case is a leaner skill. It cuts away
12:21
some of the context that it thinks is
12:22
unnecessary to make it run faster. But
12:25
it basically comes up with this idea of
12:27
this separate version or this type B
12:29
version of a skill itself. Also, it
12:31
doesn't have to be just one. Um, you can
12:33
also tell it to spin up six different
12:35
versions of scales. Then it ran the
12:37
tests and the results are actually that
12:39
my original skill used 93,000 tokens and
12:42
took 204 seconds and the optimized new
12:45
version only took 77,000 tokens and was
12:48
a lot faster with 160 seconds. But what
12:51
you can see is that it failed at
12:53
transcription extraction and the word
12:55
count was too short. And then at these
12:57
AB tests, we also have in the report a
13:00
benchmark tab here where we can compare
13:02
the outputs and see how the how the two
13:06
uh skills performed against each other.
13:08
I can say in this case it calls it
13:09
without skill but this basically means
13:10
the original skill. Of course it was a
13:13
lot faster but it filled in the
13:14
transcription and um the word count then
13:18
also gives you recommendation on what to
13:20
do based on the results. So in this case
13:21
the speed optimization are solid and
13:23
worth keeping. The two failures are
13:24
likely due to the transcript tool
13:26
behaving differently for each agent
13:28
which ran the different tests, right?
13:29
Not the skill uh changes themselves. A
13:32
rerun would confirm this. I actually
13:34
later reran it and it actually worked. I
13:36
didn't see a significant difference in
13:37
the outputs. So I updated the scale and
13:40
now it's a far faster scale at a lower
13:41
token usage. Now again, you can of
Context Engineering with A/B Tests
13:43
course use these AB tests for many more
13:44
things. For example, I also did an AB
13:46
test um for context engineering because
13:49
I know that for these copywriting skills
13:51
uh and automations, one of the most
13:53
important impacts on the output quality
13:55
is which balance of reference files or
13:58
context files that you give it. So for
14:00
example, you can also run an AB test to
14:02
define if a skill with or without a
14:05
specific reference file is more
14:07
efficient or not. So in this case, for
14:09
example, I said use the skill creator
14:11
skill, which is important to mention uh
14:13
to do an AB test on the YouTube
14:15
newsletter skill. I want to run one
14:17
skill that uses all the eight reference
14:18
files and one skill that uses all of
14:20
them, but not the voice personality
14:22
reference files. I want to assess if the
14:24
voice personality file actually improves
14:26
the cop copy or harms it. Use this
14:29
YouTube link for all the tests. And then
14:31
again, in this case, it created one new
14:33
skill without the voice personality
14:35
reference file. ran the test on the same
14:37
YouTube link and give me an output. And
14:40
in this case, of course, it's a very
14:41
subjective output. So, I'd really need
14:43
to read both of these newsletters to
14:45
make sure that one is better than the
14:47
other or if there's really a difference
14:49
and then maybe optimize the skill
14:51
accordingly. Now, these reference files
14:53
that I use for copyrightiting styles
14:55
actually come out of a lot of
14:57
experimentation and testing that I've
14:59
done before last year uh through prompt
15:01
methus, which is basically a context
15:03
engineering or prompt engineering IDE.
15:05
So, if you're building any
15:06
copyrightiting skills, I highly
15:07
recommend implementing those context
15:09
files that I mentioned to get a good
15:11
match of your tone uh of voice and
15:13
style. Again, you can find all of these
15:15
reference files uh and adapt them easily
15:17
by uh just going to my AI community or
15:19
AI accelerator. I have all these
15:20
reference files, all the skills we're
15:22
building out, including the one I showed
15:24
you. Uh we have one-on-one unlimited uh
15:26
live tech help and multiple weekly Q&As
15:28
and workshops where we dive a lot deeper
15:30
into these tools. So, if that's
15:32
interesting to you, uh definitely check
15:33
it out. We also have blueprints on how
15:35
to get your first customers in AI if
15:36
you're interested in building your own
15:37
business. So that's it for this video.
15:40
Thank you so much for watching. If you
15:41
got any value out of it, I highly
15:42
appreciate a like and a subscribe. It
15:44
really does help me. And if you want to
15:46
learn more about cloth skills, plugins,
15:47
and cloth co-work, you can also check
15:49
out the video here above.
---
# video 2
En este video



Capítulos

Transcripción
Buscar en el video
¿Qué son las nuevas Skills 2.0 de Antropic?
0:00
Antropic acaba de lanzar las skills 2.0
0:02
y es genuinamente la herramienta más
0:04
impresionante que he utilizado jamás. El
0:06
problema es que el 99% de la gente ni
0:08
siquiera sabe que existen. Siguen
0:10
repitiendo el mismo proceso día a día,
0:12
semana a semana, sin saber que una IA
0:15
hoy ya automatiza ese proceso monótono
0:17
casi que al instante. En este video te
0:19
voy a enseñar qué son las Skills 2.0
0:21
lanzada por Antropic hace unos días. vas
0:23
a aprender a configurarlas correctamente
0:25
desde el inicio e incluso vamos a crear
0:27
una desde cero con puro lenguaje natural
0:29
a través de este micrófono. Si no me
0:31
conoces, mi nombre es Daniel Carreón,
0:33
fundador de la SAS Factory, la
0:34
infraestructura donde más de 600
0:36
personas ya están creando y vendiendo
0:37
aplicaciones con inteligencia
0:39
artificial. Llevo más de 6 meses
0:40
enseñando de cloud code en YouTube
0:42
cuando nadie más lo hacía y ahora con
0:44
los avances de la nuestra productividad
0:46
se ha multiplicado por 100 si sabes
0:48
utilizar estas herramientas
0:49
correctamente. Okay, lo que les
0:50
comentaba, el problema es que a día de
0:52
hoy la mayoría de las personas siguen
0:54
repitiendo los mismos procesos monótonos
0:56
en sus computadoras, en su día a día.
0:58
Una habilidad, una skill de agentes, es
1:01
básicamente una receta, un proceso
1:03
estandarizado que lo escribes una vez y
1:06
funciona para siempre. Imagínate una una
1:08
receta que quieres que te entregues
1:10
siempre el mismo formato, el mismo tono,
1:12
los mismos pasos, las mismas reglas. Una
1:14
receta que la gente lee de forma
1:16
dinámica y te entrega resultados
1:18
consistentes. Y okay, así es como se ve
1:20
la estructura de una skill por detrás.
1:22
Puede parecer un poco técnico,
1:23
complicado, pero honestamente no lo es.
1:25
Es bien fácil, si supieran que todo esto
1:26
lo genera la inteligencia artificial, es
1:28
bien fácil a estas alturas crear estas
1:30
skills y se los voy a demostrar en este
1:31
video con puro lenguaje natural hablando
1:33
con la A. Y bueno, simplemente para
1:36
demostrar cómo funcionan esas cosas por
1:37
detrás, yo ya tengo abierto antigravity,
1:40
yo ya tengo un conjunto de skills
1:42
creadas y así es como se ven los folders
1:44
por detrás. Sí, yo puedo abrir este
1:45
folder de video visuals y así es como yo
1:47
vería, ¿no? La skill.md con las
1:50
referencias. Es bien sencillo
1:51
relativamente. Básicamente una skill
1:54
contiene un nombre y una descripción,
1:56
misma descripción y nombre que se le
1:58
pasan a las instrucciones del agente de
2:00
inteligencia artificial. El agente sabe
2:02
cuándo acceder a esta información de
2:05
forma dinámica, de modo que no saturas
2:07
su ventana de contexto en todas las
2:09
conversaciones. Simplemente accede a
2:10
esta información cuando él la necesita.
Cómo funcionan los agentes y la dinámica de archivos
2:13
Entonces, primer punto clave, el nombre
2:15
y la descripción tienen que ser
2:16
suficientemente buenos para que la gente
2:19
sepa cuándo acceder a esa información de
2:21
forma dinámica. Afortunadamente, la IA
2:23
ya es bastante buena. Ella crea todo el
2:25
resultado de inicio a fin. Pero
2:26
simplemente quiero que entiendan cómo
2:28
funciona, cómo los agentes acceden a
2:29
esta información de forma dinámica.
2:31
reciben la descripción y cuando ellos
2:33
creen que deben acceder al archivo
2:35
Markdown completo, acceden a él y el
2:38
archivo Markdown simplemente le dice
2:40
cómo utilizar ese conjunto de archivos
2:42
dentro. Entonces, así es como pudiera
2:44
verse este skill con un reference.md,
2:47
examples. Forms. Que son simplemente
2:50
distintos archivos de texto y en
2:52
ocasiones scripts de Python, código que
2:54
corre él por detrás. Okay, pero esto no
2:57
es nuevo. Las skills ya tienen desde
2:59
octubre aproximadamente, pero esta nueva
3:01
versión 2 que incluyó Antropic de forma
3:03
automática permite evaluar lo que estás
3:06
generando o lo que están generando los
3:07
agentes de inteligencia artificial.
3:09
Compara los datos para ver si se está
3:11
optimizando la precisión en los
3:13
resultados y pasas de confiar en tu
3:15
instinto, que era la primer versión a
3:17
confiar en los números. Pero de nuevo,
3:19
tú no tienes que hacer nada de esto
3:20
porque esto ya lo incluyó Antropic en
3:22
ellos ya crearon una skill que crea
3:24
skills, ¿me explico? Entonces, son los
3:26
agentes quien ya tienen todo el contexto
3:27
de esto. Para instalarlo hay de dos
Instalación rápida y configuración del Skill Creator
3:29
formas. La más fácil, simplemente tienes
3:31
que venirte a Cloud Code que si nunca lo
3:33
has utilizado, descarga Antigravity y
3:35
pregúntale al Antigravity, "Oye, bro,
3:36
¿cómo instalo Cloud Code en mi
3:38
computadora y que te y que te lo instale
3:40
de inicio a fin?" Sí, una vez que lo
3:41
instales, probablemente lo vas a tener
3:42
en la terminal, vas a querer venir a las
3:44
extensiones y te vas a buscar Cloud
3:46
Code. ¿Okay? Una vez habiendo instalado
3:48
Cloud Code, vas a estar en la misma
3:49
pantalla en la que estoy yo. A estas
3:51
alturas, ya que tienes esto, simplemente
3:53
vas a dar slash plugins. Sí. manage
3:56
plugins y vas a venir como a un
3:57
marketplace de muchos plugins que ya ha
3:59
creado Antropic y simplemente vas a
4:02
buscar skill creator. Yo ya lo tengo
4:04
aquí lo tengo deshabilitado. ¿Por qué?
4:06
Porque yo en lo personal, y esto es algo
4:08
mío, ustedes si quieren facilidad,
4:10
simplemente vénganse aquí, buscan skill
4:12
creator y les va a aparecer esta como
4:14
primeras, lo habilitan y ya lo tienen eh
4:16
activado. No, yo tengo la misma skill,
4:19
pero la bajé al repositorio. Simplemente
4:21
les voy a dejar el el link en la
4:23
descripción del repositorio en GitHub,
4:25
por si alguien está interesado. Yo la
4:26
tengo bajada a tierra porque quiero
4:28
entenderla. Sí, quiero entender qué es
4:29
lo que hace cada una de estas cosas y se
4:32
las voy a explicar para que ustedes no
4:33
tengan que hacerlo. Entonces, en pocas
4:35
palabras, en esta versión dos, Antropic
4:37
creó algo llamado Evils, que básicamente
4:40
utiliza la skill que tú creaste y la
4:41
compara con el modelo sin la skill. Si
4:44
el resultado es igual con y sin la
4:46
skill, tu skill no sirve porque a estas
4:48
alturas ya hay cosas que puede hacer el
4:50
modelo por detrás de forma automática,
4:52
¿no? Sin que tú tengas que generarle una
4:54
skill. Lo importante de todo esto al
4:55
momento de crear skills es el loop que
4:58
hacemos de retroalimentación con los
5:00
modelos. Porque por ejemplo a estas
5:01
alturas los modelos ya escriben las
5:03
primeras decisiones casi que a la
5:04
primera y las miden, las comparan, las
5:07
evalúan y simplemente nosotros estamos
5:09
ahí como como feedback, como human in
5:11
the loop, que aprobamos si la skill nos
5:13
funciona y si no nos funciona le damos
5:15
retroalimentación para repetir el bucle.
5:17
Sí, para cuando el feedback está vacío
5:19
significa que todo ya funciona perfecto
5:21
y es un proceso estandarizado que ya
5:23
tienes de aquí para la eternidad. Si
5:24
eres dueño de negocio, tienes que
5:25
aprender esto tan pronto posible. es, en
5:27
mi opinión, la habilidad más grande a
5:29
día de hoy con la inteligencia
5:30
artificial y te ha un montón de tiempo
5:32
para que tú puedas dedicárselo en otras
5:33
cosas que realmente importan, como hacer
5:35
crecer el negocio, ¿no? Okay. Y ahora
Tipos de Skills: Amplificadores vs. Preferencias
5:37
que tú entiendes cómo funciona una skill
5:39
a grandes rasgos, te voy a enseñar los
5:41
dos tipos de skills. Uno es el
5:43
amplificador de capacidades, básicamente
5:46
es enseñarle algo nuevo a la IA, como
5:50
diseñar frontend, llenar PDFs, crear
5:52
presentaciones y el segundo tipo de
5:54
skill es encoded preferences, como
5:57
preferencias codificadas, ¿no? Es un
5:59
proceso único que solo tú sigues, tu
6:02
briefing matutino, tu generador de
6:03
imágenes, tu reporte semanal. El tema es
6:06
que con el amplificador de capacidades
6:09
son skills que caducan cuando el modelo
6:12
mejora, ¿no? Probablemente con un Cloud
6:14
Opus 5, probablemente el diseño del
6:17
frontend, del skill que tú generaste va
6:19
a quedar obsoleto cuando los modelos
6:21
mejoren. El segundo tipo de skills que
6:23
muy probablemente te interesa aprender
6:25
son las encoded preferences, así es como
6:27
las llaman Tropic en la documentación,
6:29
¿no? Son como eh preferencias
6:31
codificadas. Es básicamente un proceso
6:33
único que ningún modelo conoce. Es tu
6:37
briefing matutino, el estilo, el diseño
6:39
al momento de crear y generar imágenes.
6:41
Si se lo preguntan, toda esta
6:42
presentación yo la hice con una propia
6:44
skill. Ya luego se las voy a enseñar. Ya
6:46
luego les voy a enseñar a hacer todo
6:47
esto. Em, un reporte semanal eh anichado
6:50
a tu negocio, por ejemplo, personalizado
6:53
a tus procesos internos, ¿no? A tus
6:56
propios datos. Algo que un modelo ni
6:58
Opus 10 100 nunca vas a ver, ¿no? Nunca
7:02
van a entrenar un modelo con los datos
7:03
de tu negocio, ¿no? Con tus SOPs. En
7:06
pocas palabras, son skills tuyos para
7:08
siempre y si las creas ahorita, solo es
7:11
un apalancamiento que se va apilando a
7:12
través del tiempo y que te van ahorrando
7:14
mucho, mucho tiempo. Se los prometo. Yo,
7:15
por ejemplo, ya tengo muchas skills
7:17
reales en producción que me ahorran
7:18
mucho tiempo al día, pero no las vamos a
7:21
tocar en este video. Simplemente quiero
7:22
que las tomen como prueba de concepto.
7:24
No son una demo, son ya aplicadas a mi
7:26
negocio real. ¿Okay? Y para crear un
7:29
skill a estas alturas ya lo haces tan
7:31
sencillo como simplemente hablando con
7:33
la inteligencia artificial. Y es lo que
7:34
vamos a hacer en este video, ¿okay? Sin
7:36
código, sin markdown, solo plática. Paso
7:38
número uno, oye, necesito hacer un
7:40
reporte semanal de YouTube. Paso número
7:42
dos, la IA construye la skill. Y paso
7:44
número tres, está listo para siempre. Es
7:45
un proceso repetitivo que está de nuevo
7:47
de aquí hasta el fin de la eternidad. La
7:50
IA construye sus propios SOPs. Okay,
7:52
ahora sí vamos a pasar a la acción. Les
7:54
voy a enseñar a construir skills desde
7:56
cero a través del lenguaje natural. Van
7:57
a ver qué sencillo es. Y lo vamos a
7:59
hacer con un ejemplo práctico que yo ya
8:01
quiero aplicar a mi a mi negocio, ¿no? A
8:02
mis procesos internos. Antes de empezar,
Creando una Skill desde cero en tiempo real
8:04
este es el repositorio que les
8:05
comentaba. Aquí tienen el link, se los
8:07
voy a dejar en la descripción. De todas
8:08
formas, simplemente cópienlo, péguenselo
8:10
a su agente de guía y díganle, "Oye,
8:12
instálame el skill creator si es que
8:14
quiera, ¿no? De nuevo, si no tienen la
8:16
forma más fácil que es slash plugins,
8:17
instala skill creator y por detrás ya
8:19
tiene lo mismo. E simplemente si quieren
8:21
entender esto, aquí tienen la estructura
8:24
de carpetas, ¿no? ¿Qué es lo que vamos a
8:25
hacer? Miren, esto es algo que yo
8:27
genuinamente quiero lograr y es tengo mi
8:30
propio software de Business OS, eh, y
8:33
básicamente conecté a un agente de
8:35
inteligencia artificial de cloud con mi
8:38
repositorio. O sea, este agente que
8:40
están viendo aquí tiene el mismo acceso
8:41
a la misma estructura de carpetas a
8:43
esto. La ventaja es que esta cosa yo la
8:45
tengo desde mi teléfono. Sí, es muy
8:47
similar a lo que está sacando del remote
8:49
control. Pueden buscarlo en la web, pero
8:51
yo utilicé el protocolo Agents SDK.
8:54
Básicamente es muy similar, pero entre
8:57
en en mi propio frontend, ¿no? En mi
8:59
propia interfaz. Yo desde aquí puedo
9:00
modificar y actualizar y hacer lo que
9:02
quiera, ¿no? Con este agente. ¿Qué es lo
9:03
que quiero hacer? Las mismas imágenes
9:05
que ustedes están viendo desde aquí. Yo
9:06
lo que quiero simplemente es una
9:08
habilidad que le permita a mi agente,
9:10
este agente de nuevo, estar conectado al
9:12
mismo cloud que están viendo por acá.
9:13
Eh, quiero que le permita crear esas
9:15
imágenes en un en un canvas. Sí, este
9:18
canvas también es generado con código.
9:20
Este es software propietario dentro de
9:22
mi propio Business OS. Es mi sistema
9:25
operativo del negocio. Ya luego les voy
9:27
a hablar más de todo esto, no se
9:28
preocupen. Pero bueno, pocas palabras,
9:30
es muy similar a un Excalid Draw, pero
9:32
es es código hecho por mí, ¿eh? O por la
9:35
o por mi inteligencia artificial, ¿no?
9:36
Mejor dicho. Y lo que quiero es que este
9:38
agente de IA pueda crear, o sea, a día
9:41
de hoy ya puede crear diagramas. Sí,
9:42
mira, hermano, en el donde te encuentras
9:45
ahorita mismo, crea un diagrama
9:46
sencillo, simplemente un cuadrado y
9:48
saluda a mi audiencia en YouTube. Tan
9:50
simple como eso. De nuevo, este agente
9:51
está conectado con CloudC y por detrás
9:53
tiene este skill, para quien se lo
9:54
pregunte, skill eh Canvas diagram, le
9:57
permite crear canvas. Entonces, miren,
9:59
está buscando la herramienta, está
10:01
ejecutando la skill, ejecutando el
10:03
comando y básicamente accede a esta
10:05
skill, accede a la skill de canvas
10:07
diagram y aquí tiene tal cual lo que
10:09
tiene que hacer por detrás para poder
10:11
crear, por ejemplo, los diagramas y
10:14
elementos. Lo que quiero hacer es
10:16
mejorar las capacidades de esta skill y
10:19
que no solo eso, que también le permita
10:21
insertar imágenes. Y es que verán la
10:24
presentación que yo les enseñé con
10:25
imágenes lo hice con una automatización
10:28
con esta skill que están viendo en vivo.
10:30
Básicamente lo que me permite es crear
10:33
un conjunto de imágenes con nano banana.
10:35
Ya luego les voy a enseñar todo esto.
10:37
Sí, voy a estar creándoles muchos videos
10:39
con el paso de los días. En pocas
10:40
palabras, quiero unificar esas dos ahora
10:42
mismo. Yo los videos que ya creo, miren,
10:44
eh, se se guardan aquí. Se me va ya
10:47
generadas. La misma presentación que les
10:48
mostré la tengo aquí. Sí, lo que quiero
10:51
es que estas imágenes el agente pueda
10:53
insertarlas acá. Ya creo el el el
10:55
recuadro. ¿Qué onda, YouTube? Soy Levi,
10:57
el socio estratégico de Daniel.
10:58
Bienvenidos a SAS Factory. Okay, me
11:01
gusta mucho la presentación, entonces
11:02
quiero eso. ¿Cómo lo voy a hacer? Bien
11:04
fácil. Sí, le voy a decir, "¿Qué onda,
11:06
hermano? Oye, quiero que puedas insertar
11:09
imágenes en el canvas.
11:13
Ahora mismo ya tienes una habilidad que
11:15
te permite crear esas imágenes y otra
11:18
habilidad que te permite gestionar el
11:20
canvas, crear diagramas, crear este
11:23
plantillas. Por ahora, simplemente
11:25
investiga a fondo, entiende todo el
11:27
contexto, ¿sí? Mapea el contexto de
11:29
primeras, no modifiques nada todavía.
11:30
Tan simple como eso, voy a dar enter,
11:32
¿okay? Y mientras la investiga la
11:34
información, para quien se lo pregunte,
11:35
esta herramienta que me permite
11:37
transcribir mi voz a texto fue creada
11:40
con la misma metodología que les
11:42
comparto en la SAS Factory. SAS Factory
11:44
es mi comunidad donde más de 600
11:46
miembros ya están creando y vendiendo
11:48
sus primeras aplicaciones. Noten como
11:49
Daniel hizo su primera venta con SAS
11:51
Factory. Alberto creó su primera
11:53
aplicación desarrollado con la SAS
11:54
Factory. Claudio hizo su primera venta
11:56
con la SAS Factory. Esto tiene un día
11:58
literalmente. Quiero que vean la
12:00
cantidad de logros que están teniendo
12:01
las personas dentro de la comunidad.
12:03
Este mismo láser que están viendo fue
12:05
creado con la misma metodología que les
12:07
comparto en la SAS Factory. Para todo
12:09
aquel que esté interesado, les voy a
12:10
dejar el link de mi comunidad en la
12:11
descripción. Dentro vas a encontrar el
12:13
curso definitivo para que puedas
12:14
construir estas cosas en tiempo récord.
12:17
Incluso la misma plataforma que estás
12:18
viendo ahora fue creada con la misma
12:20
metodología que te comparto. Todo esto
12:22
vive en mis propios servidores. Yo no te
12:24
voy a enseñar a construir aplicaciones
12:26
mientras te vendo mi comunidad school.
12:29
¿Por qué no? porque sería
12:30
contradictorio, sería irónico, ¿no
12:32
crees? En fin, si estás interesado, te
12:33
lo voy a dejar en el primer link en la
12:35
descripción para que te unas y crees tus
12:37
primeras aplicaciones como cientos de
12:39
usuarios ya lo están haciendo en tiempo
12:40
récord sin saber nada de código, pero
12:42
okay, ya la inteligencia artificial
12:44
terminó, ya mapeó el contexto, lo que ya
12:46
existe, el canvas, la skill para generar
12:49
imágenes, la API de draw, lo que falta,
12:52
el 10%, ya está la mayoría de cosas. El
12:54
flujo actual funciona bien, pero con
12:57
fricción. Sí, para insertar imágenes en
12:59
el canvas dice que ya funciona. Okay,
13:02
interesante. Toma las riendas de esto.
13:03
¿Qué me recomiendas? Sí, quiero que Levi
13:06
pueda insertar las imágenes que él mismo
13:09
puede generar o que pueda jalar de la
13:11
propia base de código las imágenes ya
13:13
generadas, por ejemplo, en la carpeta de
13:16
de contenido, videos. ¿Qué me
13:17
recomiendas? Y entonces, miren, yo no
13:19
voy a recrear la skill desde cero. Ya
13:21
tengo este skill y ya tengo las
13:22
referencias. Simplemente quiero que crea
13:24
un nuevo archivo Markdown que se
13:25
encargue de eso y le voy a decir, "Okay,
13:26
entonces encárgate tú del resto. Ya
13:28
tengo la skill de Canvas Diagram y lo
13:31
que quiero es crear un nuevo archivo
13:33
markdown en el folder de referencias que
13:36
me permita justamente esto. Puedes
13:38
encargarte de todo de one shot. Eh,
13:41
además añádele a las skill.md eh para
13:44
que la gente cuando acceda a este
13:45
markdown sepa cómo tratar lo lo nuevo
13:47
que estamos creando, ¿vale? Haz todo de
13:49
one shot y es más tu valida end to end.
13:51
crear la utiliza la imagen de
13:53
referencia. Tú también tienes la misma
13:55
skill y genera o más bien inserta una
13:58
imagen que encuentres aleatoria de de
14:00
esta base de código. ¿Qué te parece? Eh,
14:01
voy a recortar esto porque probablemente
14:03
se va a tardar un ratito en lo que
14:04
genera la skill. Luego la va a probar,
14:06
va a ver si funciona o no, lo mismo que
14:08
que les que les enseñé y va a ser todo
14:10
esto. Sí, algo clave. Ustedes no tienen
14:12
que entender cuestiones técnicas porque
14:14
a día de hoy el técnico es la
14:16
propiedadía. tus habilidades son de
14:18
comunicación, son de entendimiento de
14:21
sistemas, son de resolución de
14:23
problemas, si es que los hubiera, ¿no?
14:25
Porque a de hoy la idea ya es tan
14:26
avanzada que honestamente la mayoría de
14:28
las cosas casi que las consigo de one
14:29
shot. Lo que le digo lo cumple, eh, y se
14:33
los se los firmo. Yo estoy casi 100%
14:35
convencido de que esto va a funcionar
14:37
cuando termine. Sí. Y si falla,
14:39
probablemente se va a deber a fallas en
14:41
mis instrucciones, no tanto a las
14:42
capacidades de la IA. Entonces, bueno,
14:44
eh lo voy a dejar así. No voy a hacer
14:46
recortes para que vean que no voy a
14:47
modificar nada y simplemente voy a
14:49
deshabilitar mi cámara y voy a
14:51
multiplicar la velocidad para que
14:53
ustedes puedan ver en vivo cómo trabaja
14:55
y genera todo esto de one shot
14:57
básicamente.
15:03
Okay, miren esto. La validación en trend
15:05
la gente incluso está abriendo el
15:07
navegador. Quiero que vean esto, y no va
15:09
a parar hasta que no se asegure que en
15:12
el front-end funciona. Y ese es el
15:14
secreto de todo. Si tú permites que la
15:16
IA tenga todas las variables al sistema
15:18
y puedes cerrar ese bucle, la pregunta
15:21
deja de ser si sí o si no puede hacerlo,
15:23
sino cuánto tiempo le va a tomar, ¿no?
15:25
Entonces, yo te firmo algo. Ahorita me
15:26
parece que que no encuentra el canvas,
15:29
pero eh se va a quedar trabajando de
15:31
inicio a fin hasta que lo consiga.
15:33
Entonces, miren, encontró la ruta, ya
15:35
actualizó ahora sí correctamente la la
15:37
pantalla. Él está controlando el
15:38
navegador y insertó él solo la imagen.
15:41
Entonces, miren, al parecer dice, "Ah,
15:44
la página cargó. El canvas, es un canvas
15:46
HTML que no aparece en el snapshot. Tomo
15:49
screenshot para verificar visualmente.
15:52
Va a tomar un screenshot de lo que está
15:53
viendo ahora mismo. Miren, incluso
15:55
podemos ver el resultado del screenshot.
15:56
A ver, a ver si lo podemos encontrar por
15:58
aquí. Sí, eh, creo que va a estar por
16:00
aquí. Uy, miren la cantidad de imágenes
16:02
que que tiene. Sí, miren, aquí tenemos
16:04
la la imagen tal cual. Sí, este es el
16:05
screenshot que tomó. Este screenshot se
16:08
le pasa al propio modelo y entiende lo
16:11
que está pasando, ¿no? Entonces, por
Validación del flujo y automatización total
16:13
alguna razón dice loading, si yo me voy
16:16
a mi propia plataforma y actualizo,
16:19
miren, si actualizo la la pantalla, yo
16:21
ya puedo ver que tengo este test image
16:23
injection, ¿sí? y ya puede inyectar
16:25
imágenes. El tema es que está cargando y
16:28
por alguna razón no termina de cargar,
16:30
¿no? Entonces, probablemente esto se
16:31
debe a un error que cometió, pero es lo
16:33
que les comento, o sea, se va a quedar
16:34
trabajando y hasta que no valide que
16:36
funciona. Ese es el secreto de toda mi
16:38
productividad. Si vieron que he podido
16:40
crear una plataforma réplica de de
16:42
school, si vieron que he podido crear un
16:44
business OS que me permite literal
16:46
monitorear, gestionar todo mi negocio
16:48
desde una interfaz visual como la que
16:50
están viendo y que estamos construyendo,
16:52
lo que están viendo ahorita, es porque
16:54
entendí que si cierro el bucle, la ya se
16:56
encarga de todo. Yo a estas alturas lo
16:58
que hubiera hecho hubiera hubiera
17:00
generado estas instrucciones y me
17:01
hubiera ido al gimnasio. Sí. Y yo cuando
17:03
volví cuando hubiera vuelto ya esto
17:06
hubiera estado terminado. Ahí son unos
17:08
secretos que les comparto, pónganlos en
17:10
práctica y les juro que les van a
17:11
cambiar la vida. Entonces, miren, yo no
17:13
estoy tocando nada. Él encontró el
17:14
error, lo está actualizando y tan simple
17:17
como eso, sí, vamos a esperar un poquito
17:18
más. Probablemente haga un recorte para
17:20
que para que no se vuelva tan tedioso. Y
17:22
miren, es lo que les digo, se dio cuenta
17:24
de que no está cargando la imagen y está
17:26
modificando el código para resolver ese
17:28
problema. Sí, si todo esto te está
17:30
volando la cabeza, considera suscribirte
17:32
porque todo el contenido que vas a ver a
17:33
partir de hoy lo voy a enfocar 100%
17:35
relacionado con Antropic, las skills
17:37
cloud code, porque en mi opinión y
17:39
durante los últimos meses ha sido la
17:41
herramienta que más apalancamiento me ha
17:43
dado en mi negocio y quiero enseñarles a
17:45
utilizarla de la forma correcta.
17:47
Actualmente en habla hispana casi no hay
17:48
nadie hablando de esto y en mi opinión
17:50
es una de las herramientas más
17:51
importantes en esto de la inteligencia
17:52
artificial. Así que suscríbete y déjame
17:54
saber en los comentarios qué próximo
17:56
video relacionado con esto te gustaría
17:57
ver. Sigamos con el video.
18:01
¿Qué tal, amigos? ¿Cómo están? Hemos
18:03
vuelto. E la verdad es que estaba
18:04
tardando un poquito más de lo que
18:06
esperaba y le dije, "¿Sabes qué? Me
18:08
tengo que ir. Quédate trabajando tú por
18:09
detrás." Miren, les voy a mostrar
18:11
literalmente las instrucciones que le
18:12
di. Pero básicamente le dije, "Me tengo
18:14
que ir, quédate trabajando." Y la gente
18:15
se quedó ahí investigando a fondo,
18:17
planeó por fases y en un bucle infinito
18:19
de 0 a 100 terminó todo. Sí, yo volví y
18:23
me dijo, "Mira, ya está terminado." Y
18:25
aquí probando, o sea, directamente ya
18:27
está funcional esto. Y me vuela la
18:28
cabeza. Okay, ¿cómo funciona esto?
18:30
Recuerden, yo esto lo conecté con mi
18:32
base de código. Esto es mi business o
18:34
esto tiene una muchísima oportunidad.
18:36
Luego les voy a estar platicando más de
18:37
todo esto. Suscríbanse si están
18:38
interesados. Eh, les voy a enseñar cómo
18:40
conectar su negocio con inteligencia
18:43
artificial, ¿no? Cómo crear un sistema
18:44
operativo donde un agente de
18:46
inteligencia artificial, en este caso
18:47
Cloud Code, tiene acceso a todas las
18:49
variables dentro del negocio. En ese
18:51
sentido, ahora este agente ya tiene la
18:53
habilidad, tiene la capacidad, tiene la
18:55
skill que le permite insertar imágenes,
18:58
le permite crear imágenes con nano
19:00
banana e insertarlas en este diagrama.
19:02
digo, es una skill muy simple, pero al
19:05
menos a mí lo personal que que tengo
19:07
este software propietario, bueno, si se
19:09
lo preguntan, esto no es Excali Drraw,
19:10
no es este Miro, no es Teledropow, no es
19:13
Figma, es una aplicación creada con
19:16
código por mí, por inteligencia
19:18
artificial, ¿no? Entonces, bueno, ¿cómo
19:19
funciona? Pues es como un Excalidr
19:21
normal, tú puedes dibujar total, esto me
19:23
gusta porque yo lo puedo adaptar a como
19:25
a mí se me antoje. La verdad es que yo
19:26
ya tenía una inserción de Excalidrow, es
19:29
de código abierto y lo tenía aquí como
19:31
una como una pestaña, pero me limitaba
19:33
en algunas cuestiones y dije, "A la ver,
19:35
a la voy a voy a hacer mi propia
19:37
aplicación." Y la verdad es que me me la
19:39
aventé en un día, o sea, se lo juro.
19:40
Incluso evidentemente hay algunas
19:42
algunos detalles que pudiera
19:43
implementar, pero o sea, ya es una
19:46
aplicación funcional, ¿saben? Lo que yo
19:47
quiero compartirles es justamente cómo
19:50
le acabamos de dar la la habilidad a
19:51
nuestro agente para poder insertar
19:53
imágenes. Entonces, qui quiero que lo
19:54
vean. Hermano, ¿cómo estás? Oye, eh,
19:57
investiga en la base de código. Eh, creo
19:59
que hay un un fold llamado contenido
20:01
YouTube dentro de un fold de Skill 2.0 o
20:04
algo así. Y quiero que investigues, hay
20:05
como 11 imágenes. ¿Puedes hacerme el
20:07
favor de insertar la número tres dentro
20:10
de este diagrama? digo, yo sé que es una
20:12
prueba quizá un poco tonta para un
20:14
video, pero a mí en lo personal yo tenía
20:17
la intención de poder trabajar con mis
20:19
agentes, con este agente que se los juro
20:21
tiene acceso a todo mi negocio y ustedes
20:22
lo van a ver en vivo. Eh, pueden ver
20:24
cómo está ejecutando una tool. Eh, igual
20:26
si quieren, bueno, es que no quiero
20:27
desviar el video, ya se lo voy a mostrar
20:29
en otro en otra ocasión, pero esta gente
20:32
tiene acceso a esta base de código
20:34
totalmente, tiene acceso a distintos
20:36
MCPs que le permiten acceder a mi base
20:38
de datos, distintas bases de datos,
20:40
porque tengo como cuatro bases de datos
20:41
en esta aplicación. Puedo abrir el
20:42
navegador desde desde esta interfaz.
20:44
Miren qué loco. Yo simplemente tengo que
20:46
dejar prendida mi computadora y desde mi
20:48
teléfono decirle, "Oye, trabaja."
20:50
Mientras yo estoy en el gimnasio o o
20:51
estoy en la calle o donde sea. Entonces,
20:53
miren, pueden ver cómo está ejecutando
20:54
los comandos. ¿Sabes que lo único que me
20:56
preocupa? Okay. Eh, me preocupa que no
20:58
hayas utilizado la skill, quizá mal la
21:00
mía, me refería a que las insertes en
21:02
este canvas. Y bueno, creo que es una
21:04
palabra clave canvas cuando detecta la
21:07
skill. Por eso les comenté al principio
21:09
de este video que es muy importante eh
21:11
la descripción correcta y los nombres
21:14
correctos porque es lo que le pasamos en
21:15
las instrucciones a la gente, ¿no? Ahora
21:17
sí, miren, esto es lo que les decía,
21:18
¿sí? Ahora sí ejecutó la skill, ahora sí
21:20
la leyó. Yo ya con esto yo me aseguro
21:22
que esto que están viendo aquí, Canvas
21:24
Diagram, fue lo que se le pasó como
21:26
contexto. Me están aquí, miren, Cloud
21:28
Skills. Esta fue la la nueva skill que
21:30
creamos, ¿no? Canvas Diagram. Si me voy
21:32
aquí a campus diagram skill, esta
21:33
simplemente la actualizó, no creó una
21:35
nueva skill, perdón, simplemente añadió
21:37
un nuevo una nueva referencia llamada
21:40
image injection, ¿no? Que le permite
21:43
inyectar imágenes de forma dinámica. Eh,
21:45
la verdad es que no me pregunten qué hay
21:46
relacionado con el código porque yo no
21:47
hice nada. Todo se encargó la
21:49
inteligencia artificial aquí por detrás.
21:51
Eh, miren, ya lo insertó. Sí, insertó la
21:54
imagen número tres y quiero que vean
21:55
esto, sí, o sea, literalmente lo que
21:57
hizo la gente por detrás fue venirse a
22:01
contenido, videos, proyectos, eh skills
22:03
2.0 generadas, creo que fue y le dije
22:05
que inertara la tres, ¿no? Esta tal
22:07
cual. Y si me ve acá, en efecto, insertó
22:10
la número tres. Esto está impresionante.
22:12
Sí, porque esto esto no no no lo tengo
22:14
con con Excalid Draw o con Miro o con
22:17
Teledraw, ¿no? Les digo, puede parecer
22:19
un poco tonta la habilidad, pero a mí al
22:22
menos que utilizo diagramas visuales que
22:24
me ayudan mucho, tener una gente que me
22:26
los genera y que encima me los inserta,
22:28
que digo encima tiene habilidades de de,
22:30
o sea, puede crear eh diagramas mermite,
22:32
puede crear este propios diagramas
22:35
utilizando las mismas figuras que
22:36
tenemos aquí, ¿no? como se los mostré en
22:37
un inicio. Entonces,
22:40
yo considero yo que tiene mucho
22:41
potencial todo esto. Y bueno, díganme
22:43
qué opinan, qué tal les parece todo esto
22:44
digo, son solo una prueba de concepto.
22:46
Vieron que la hicimos con meras palabras
22:48
naturales, en ningún momento utilizamos
22:49
código y si en algún momento hubiera
22:51
llegado a fallar, yo le copio la
22:53
habilidad, se la vuelvo a pegar a esta y
22:55
le digo, "Oye, hasta que funciones no
22:57
vas a parar." Sí. Y esto es algo que ya
22:59
se queda para la eternidad. En esta
23:00
ocasión solo es una prueba de concepto
23:02
donde la gente ya tiene la capacidad de
23:03
insertar imágenes, pero tengo muchas más
23:06
habilidades, por ejemplo, que que me
23:07
ahorran muchísimo tiempo. Les voy a
23:09
estar trayendo muchos mucho contenido
23:11
relacionado con las skills, porque en mi
23:12
opinión son la habilidad más grande de
23:14
inteligencia artificial hasta ahora.
23:16
Genuinamente se los digo, nada hasta
23:18
ahora nos había podido ahorrar tanto
23:20
tiempo como nos había permitido ser más
23:23
productivos que estas cosas. Por
23:26
ejemplo, eh probablemente al principio
23:28
del video vieron que yo les inserté, que
23:30
les que les compartí una presentación
23:31
con imágenes, ¿no? Esas mismas imágenes
23:33
son las que les estoy pasando ahorita
23:35
mismo. Sí, estas imágenes las recuerdan.
23:37
Todas estas las generé con una propia
23:39
skill. Entonces, estas mismas imágenes
23:40
que creamos con una automatización, con
23:42
una skill que el propia gente diseñó,
23:44
fue diseñada a partir de mero lenguaje
23:46
natural. Esto es lo impresionante, que
23:48
la gente de allá afuera no está viendo
23:49
la oportunidad, pero nunca había sido
23:51
más fácil diseñar estos sistemas que
23:53
automatizaran nuestro tiempo, que como
23:55
dueño de negocio es muy limitado,
23:57
¿sabes? O sea, tienes que estarlo
23:59
dedicando a escalar el negocio y hay
24:01
muchas cosas que te roban el tiempo. Si
24:03
tú las puedes automatizar con este tipo
24:04
de sistemas, te lo juro que el cielo es
24:06
el límite al momento de escalar tu
24:08
negocio. Esa skill que que pudieron ver
24:10
es esta misma, video visuals, ¿no? Pero
24:12
es esto es lo que se le pasa a las
24:14
instrucciones de la gente, al cerebro.
24:16
Eh, dice, "Usar cuando Daniel proveea un
24:19
guion, un transkrip o una idea de video
24:21
y quiera un conjunto de imágenes
24:22
didácticas." Ta ta. le dice tal cual el
24:24
diseño, le dice todo por detrás, los
24:26
colores y cuándo usar cada uno de de
24:28
estos distintas referencias, ¿no? Le le
24:31
referencia alguna parte estos dos
24:32
referencias. El número uno es le inserta
24:35
el video de forma automática y el número
24:37
dos probablemente vieron un carrusel al
24:40
principio del video. Ese mismo carrusel,
24:42
miren, eh, me voy a venir aquí la
24:43
sección de cursos. Aquí miren, cloud
24:45
code skills y ese mismo carrusel se le
24:47
inserta, o sea, sin yo tocar esto lo
24:49
inserta porque todo de nuevo todo es
24:51
software propietario, o sea, la
24:53
plataforma que tengo de la comunidad es
24:55
esta y las imágenes están aquí. Todo
24:57
está en la misma base de código.
24:59
Entonces yo si le digo, no sé cómo, o
25:01
sea, no me preguntes las cuestiones
25:02
técnicas porque la ya se encargó de
25:04
todo, pero yo simplemente le dije,
25:05
inserta eh las imágenes aquí en el
25:07
carrusel. Y funcionó. Miren, y yo lo que
25:09
vieron al principio de la presentación
25:11
fue básicamente algo que hice en no sé o
25:13
10 minutos. ¿no? Entonces, eso es todo
25:16
lo que quería compartirles, mi gente.
25:17
Espero entiendan por qué el canal lo voy
25:19
a estar enfocando 100% en estas cosas,
25:22
en cloud, sobre todo. Ahorita el mercado
25:24
finalmente le está viendo la oportunidad
25:25
y yo llevo ya más de 6 meses hablándoles
25:27
de esto, incluso 2 años, 2 años desde
25:30
cursor, ¿no? Mi gente, agradezco su
25:32
tiempo, gracias por llegar hasta acá.
25:33
Suscríbanse si esto les gustó, denle me
25:35
gusta, compártanlo, comenten eh qué les
25:38
gustaría ver relacionada con Cloud Code,
25:39
¿no? Evidentemente agentes de íen local
25:41
y todo esto. Y nos vemos en un siguiente
25:43
video. Agradezco su tiempo, su atención
25:45
y todo. Dale, nos vemos.
-> github:[https://github.com/anthropics/skills/tree/main/skills/skill-creator]
---
# video 3
En este video



Capítulos

Transcripción
Buscar en el video
Update #1: Loops for Short-Term Tasks
0:00
If you're using claw code, these four
0:02
brand new updates completely change what
0:04
you can build. Loops, scheduled tasks,
0:07
Google workspace access, [music] and
0:09
built-in skill testing or skills 2.0.
0:11
So, instead of watching four separate
0:13
videos to figure these out, here's the
0:14
shortcut. In the next 10 or so minutes,
0:17
I'll show you exactly what each feature
0:18
does, when you'd actually use it, and a
0:21
quick demo of all four. So, let's get
0:23
straight into it. So up until now, if
0:25
you wanted claw code to check on
0:26
something repeatedly, you had to keep
0:28
coming into the interface, prompting it,
0:31
come back, ask again, come back, ask
0:33
again. But the new /loop feature changes
0:36
that completely. So it says here, run a
0:37
prompt or slash command on a recurring
0:39
interval. So loop lets you schedule
0:41
recurring prompts inside your current
0:43
session. So you can say something like
0:45
/loop every 10 minutes. Check my inbox
0:47
for important emails. And when we fire
0:50
that, Claude's going to create a chron
0:52
job that fires automatically and the
0:54
prompt's going to be put into claude
0:55
code every single 10 minutes. And it's
0:57
just going to run. We don't need to
0:58
touch it. You can see that chron create
1:00
being created there. And you can
1:01
literally write anything in natural
1:03
language. And it will set up and use the
1:05
skills that you want it to use too. So /
1:07
loop everyday check my YouTube for new
1:09
videos and then run my content
1:10
repurposing skill. Inside my skills
1:13
library, we've got the marketing content
1:15
repurposing skill to create a newsletter
1:17
and a tweet. and it's gone and created
1:19
that too. You can see that that's put
1:21
all the scheduled tasks in this
1:23
scheduled tasks document. Or you can say
1:25
something like in one minute remind me
1:27
to talk about one-off reminders. And
1:28
what that's going to do is go and set up
1:30
a single occurrence reminder. And in a
1:32
minute, it's going to give us that
1:33
notification.
1:35
And after the longest minute of my life,
1:37
we've got the reminder up here, claw
1:38
code reminder. Talk about one-off
1:40
reminders. So the point is reminders are
1:42
one-off. Loops are recurring tasks. both
1:45
get created the same way under the hood
1:47
using chron jobs. So if we go to the
1:48
claw code docs, we can see that there's
1:51
three tools that it uses. Chron create,
1:52
chron list, and chron delete. They're
1:54
exactly as they sound. So basically cron
1:56
is a notice for some sort of command to
1:59
run at a given time. And that's exactly
2:01
what it stands for. Command run on
2:03
notice. And just for quick reference,
2:04
it's done using these cron expressions
2:07
which effectively are different symbols
2:09
for different time values. That's it.
2:11
Now let's talk about the limitations. So
2:13
loops expire after 3 days. That is
2:15
probably the biggest limitation so far.
2:17
And that's a safety thing. So you don't
2:19
accidentally have 20 loops running
2:20
forever. They also only live in your
2:22
current session. So if you close the
2:24
terminal, they're completely gone. And
2:26
they don't even catch up. So if the
2:27
session was closed when a loop was
2:28
supposed to fire, it just disappears and
2:30
never runs again. So think of loops as
2:32
help me right now on this project. like
2:34
watch my inbox for important emails,
2:37
track changes across a sprint, and
2:39
anything where you need clawed checking
2:41
in for the next few hours or days. It's
2:43
not long-term. So, what if you do need
2:44
something that runs every week or every
2:46
morning? That's where scheduled tasks,
2:48
the second update, comes in. So, loops
2:49
are great for short bursts, but if you
2:51
want claw code to do something every
2:53
single morning or every Monday, for
2:54
example, you need something more
Update #2: Scheduled Tasks for Long-Term Automation
2:56
permanent. Many of you will think of
2:58
this as workflows, much like you build
2:59
in a tool like nan. So, scheduled tasks
3:01
are exactly that. You set up a task with
3:03
a prompt, choose the model, choose the
3:06
schedule, whether it's daily, weekly,
3:07
hourly, whatever, and it just runs. So
3:09
every time it fires, it's going to start
3:11
a fresh instance, unlike /loops, which
3:13
sits in one instance. It's going to read
3:15
your project files, run through the
3:17
skills it needs, and then run the
3:18
command. And it's going to stop the
3:20
session once it's completed. So
3:21
something I would use, for example, is
3:23
/cched every day, check my YouTube for
3:25
new videos, and then run my content
3:27
repurposing skill to create a newsletter
3:29
and tweet. And I have to run this in the
3:31
desktop app either in code using the
3:33
schedule or I can run this directly in
3:35
co-work by hitting new tasks on schedule
3:38
tasks. Here you can see we add a name,
3:39
we add a description, we add a prompt
3:41
and here we don't need the slash
3:42
schedule. We say repurpose videos
3:44
repurposes new YouTube videos and then
3:45
tell it what to do. And we can obviously
3:47
then add the daily frequency of 9:00
3:50
a.m. Choose the model. Select the folder
3:52
to work in if we want and hit save. And
3:54
that's going to create a scheduled task
3:56
that's going to run every single day.
3:57
And if we go to customize, we go to our
3:59
skills, it's going to leverage because
4:01
of the descriptions that we've used in
4:03
our skills, the YouTube tool to actually
4:05
pull information from my YouTube and
4:07
then the marketing content repurposing
4:09
skill with all of the references to
4:11
different copywriting techniques and
4:13
splitting it out per platform from this
4:15
skill too. So now all of this sounds
4:17
really good, right? But the key
4:19
limitation right now is as you've seen
4:21
that you can only use this inside the
4:23
desktop app inside the clawed code or
4:26
claude co-work interface. So not in the
4:28
terminal or not in VS code extensions.
4:31
But knowing how fast anthropic is
4:32
shipping at the moment. I'd expect that
4:34
to change very soon. The other thing
4:36
your computer has to be on and the app
4:38
has to be open. But unlike loops if you
4:40
do miss a run it does actually catch up
4:42
and run the miss task when you reopen
4:44
it. So it doesn't just disappear. So
4:46
that's quite nice. So loops for right
4:48
now, schedule tasks for every single
4:50
day. And between the two, Claude Code
4:52
will now never stop working. So core
4:54
code can run on a schedule and check in
4:56
on things automatically. But there's one
4:57
area that's been a massive, massive gap
4:59
in Claude Code skills up until now, and
5:02
that is getting it to actually work with
5:03
your Google Workspace. So if you have
5:05
ever tried to get Claude Code to create
Update #3: Full Google Workspace Integration
5:07
a Google Doc or manage your files
5:09
through the built-in skills, you'll know
5:11
this pain. For some reason, you can only
5:13
manage emails and your calendar. But so
5:16
many of us work in the Google workspace
5:18
that it needed a critical update to
5:20
interact with Google Drive. You can see
5:21
claw code has no good MCP server for
5:24
Google Drive and can't interact with the
5:25
claw code desktop. And Rich here just
5:27
wanted one that could set up an MCP
5:29
server to list, read, write, and modify
5:31
Google Docs directly and have it work
5:33
with minimal setup, not having to go
5:35
through the APIs. Now, this one's not
5:37
strictly a claw code update, but it's
5:39
still really important. And good news
5:41
because Google just released an
5:42
open-source workspace command line
5:45
interface or CLI that changes
5:47
everything. So, it's one tool that gives
5:48
Claw Code access to your entire Google
5:51
ecosystem. So, thinking Drive, Gmail,
5:53
Calendar, Doc, Sheets, Slides,
5:55
absolutely everything. And it comes with
5:56
over 100 built-in recipes that Google
5:59
have already set up. So, it makes it
6:01
super simple to do anything like create
6:03
a document. And I know this says this is
6:04
not an officially supported Google
6:06
product, but this is just because it's
6:07
in beta phase. The setup is super
6:09
simple. You can either install it
6:10
directly in your terminal or literally
6:12
just take it directly to cloud code and
6:14
ask it to set up this Google command
6:16
line interface. It's going to guide you
6:17
through the whole setup process. And the
6:19
way it creates documents is going to be
6:21
completely different. So if you've ever
6:23
created documents through a tool like N,
6:25
you'll have seen that the documents come
6:26
out with raw markdown formatting and you
6:28
actually have to make API calls to make
6:30
it look good. This in contrast is
6:32
running bash commands that talk directly
6:34
to Google. So you get properly formatted
6:36
docs with headers, images, links,
6:38
everything. So, it's the full package
6:39
that is being delivered here. So, let's
6:41
use our content repurposing system to
6:43
produce a markdown formatted Google Doc
6:46
now to show you. And there you go. You
6:47
can see that we've got a properly
6:48
formatted markdown document that's just
6:51
been created with one install, the
6:52
Google command line interface. So, we've
6:54
got loops, we've done scheduled tasks,
6:57
and now we have Google Workspace access.
Update #4: Build & Test Better Skills with Skills 2.0
6:59
But the update I'm most excited about is
7:01
the one that makes every skill you build
7:03
dramatically better, much, much quicker.
7:06
And by the way, if you're building
7:07
skills and want a head start, I've got a
7:09
full library of production ready skills,
7:11
reference files, and frameworks inside
7:13
my Aentic Academy in the description.
7:15
So, it will help you spin up brand voice
7:17
files, ICP templates, copywriting
7:18
references, the lot. Plus, you get
7:20
one-on-one help if you get stuck. So,
7:22
the links in the description if you want
7:23
to check that out. Right, let's move on
7:25
to skills 2.0. So, if you've been
7:27
building skills inside Claw Code so far,
7:30
you would build a skill, you run it, the
7:32
output's okay, but not brilliant. So you
7:34
tweak it, you run it again, and this
7:36
continues until you get something
7:37
possible. So you're always iterating on
7:39
it, and you don't really know what's
7:40
working and what isn't. But Skills 2.0
7:42
is designed to fix that with built-in
7:44
evaluation and testing. And this is a
7:46
muchneeded update. So Anthropic actually
7:48
went and updated the skill creator
7:50
skill, so their own skill creator skill
7:52
to include proper evals. And what that
7:54
means in plain English is you can now
7:56
automatically test your skills against
7:58
specific criteria and get scored results
8:00
back. So, not just simple did it work or
8:03
not. You get actual grades on things
8:04
that matter to you. And here's how I'd
8:06
recommend using it because if you just
8:08
say run some tests, you'll get generic
8:10
results that aren't very useful. So, the
8:13
key is being specific about what you're
8:14
actually trying to optimize the test
8:16
for. So, let's walk through a process.
8:18
First, you're going to build your skill
8:19
with a solid framework. So, you can
8:21
actually use the skill creator skill as
8:23
it sounds to do that. You're going to
8:24
give it a clear name, a trigger
8:26
description that's really descriptive,
8:28
and define the goal of it. You're going
8:29
to specify which tools or connectors it
8:31
needs. You're going to list your
8:32
reference files, your brand voice, your
8:34
ICP, and actually connect those inside
8:37
the skill.md description. And then
8:38
you're going to lay out step by step the
8:40
process you want it to follow. And that
8:42
is ultimately the skill.md. So you're
8:44
going to include things like where you
8:45
want the human in the loop checkpoints
8:47
and where the output should actually be
8:49
saved. And that will get you to a good
8:50
first version. But as you know, they're
8:52
never finished on the first try. So most
8:54
good skills go through many iterations
8:56
before they really start to solve your
8:57
problems. And that's exactly what eval
8:59
are designed for, to speed up that
9:01
learning cycle. So, let's use my
9:03
marketing copywriting skill to demo
9:04
this. So, instead of saying, "Run some
9:06
tests on my copywriting skill," you say
9:09
something like this. Run a new test
9:11
optimized for making sure my copy
9:13
follows the persuasive techniques listed
9:15
in my persuasion toolkit reference file.
9:18
And you can see in the marketing
9:19
copywriting skill, we've got the
9:20
persuasion toolkit.md as a reference
9:22
file. The criteria are XY Z. So it might
9:25
be does it always use the reference file
9:27
firstly? Does it use curiosity and open
9:29
loops which are actually listed inside
9:31
the persuasion toolkit? And how often is
9:34
it using proof or founderled stories
9:36
which is another thing that's listed in
9:37
that persuasion toolkit. So is it using
9:39
that properly is basically what we're
9:41
asking it to evaluate here. And then
9:43
what we're doing is testing it on this.
9:44
We're testing it on writing landing page
9:46
copy for my school community. And we're
9:48
going to get it to do it five times and
9:50
test it against that exact criteria. And
9:52
what it's going to do is go out and
9:54
actually do the test using the skill and
9:56
come back with a proper framework of
9:58
evaluation of how it performed. So it's
10:00
successfully loaded that meta skill
10:02
creator skill which is just a renamed
10:04
version renamed and improved version of
10:05
the skill creator skill through
10:07
anthropic and it's starting to run the
10:09
evaluation test now. And you'll notice
10:11
we're not trying to optimize for like
10:12
six things at once because there would
10:14
be way too many moving parts. So what
10:16
we're doing is picking one to three
10:17
things. We're testing it, we're then
10:19
improving it and then moving on to the
10:21
next one. So let's have a look at what
10:22
they come back with. And by the way, the
10:24
email runs multiple variations in
10:26
parallel using sub aents. So it happens
10:28
pretty quickly and it's going to score
10:30
each one against your criteria and give
10:32
you a structured report, a HTML report
10:35
that we can actually go through. So you
10:36
can see five agents launch grade
10:38
copywriting run 1 2 3 4 and five. And
10:41
it's going to come back with a really
10:42
nice click through that we can see the
10:44
criteria and actually improve our skill.
10:46
So this is where the brilliance comes in
10:48
because actually this skill creator
10:50
evaluations will spin this up into a web
10:53
page that we can go and look at all of
10:54
the landing page outputs. So we have the
10:57
prompt that was originally put in and we
10:59
can obviously test it also with and
11:01
without skills and we'll come to that in
11:02
a moment. And it's got the outputs and
11:04
we can flick through between the
11:06
different outputs and even go down to
11:08
this formal grades section here. So,
11:10
it's saying it's not used curiosity
11:12
gaps. At least two instances where a
11:13
result or discovery teased without
11:16
immediately revealing it, creating an
11:17
information gap the reader needed to
11:19
close. And it's gone in to say the copy
11:20
lacks genuine curiosity gaps that
11:22
sustain across multiple sentences. So,
11:24
what this means is actually if we wanted
11:26
curiosity gaps to actually be abided by
11:28
then, then we need to improve either the
11:30
skilled MD file which is referencing
11:32
that information in our persuasion
11:34
toolkit or place more emphasis on that.
11:36
So, you can see that actually this is
11:37
pretty poor. 50% on this run. Six pass,
11:40
six failed of 12 there. But it gives us
11:42
a really good idea with actual examples
11:44
of how to improve our skills. So this is
11:47
a skill that I've whacked up quickly
11:48
yesterday. And you can see that it needs
11:50
improvements if those curiosity gaps and
11:52
open loops were really important for my
11:54
copyrightiting. We can then also go to
11:55
the benchmark. We can see how long each
11:58
run took to take, how many tokens plus
12:00
or minus each run took to take. And
12:02
we've obviously run five here with the
12:04
skill and none without the skill here to
12:06
compare. And we can see for each run the
12:08
evaluation breakdown of what passed and
12:11
what failed for each run here.
12:12
Thankfully, it's also assessed it
12:14
against other criteria. So these were
12:15
always passed. So in five out of five
12:17
times, it makes the pain concrete. It
12:19
digs to the emotional benefit, but
12:21
sometimes we don't have that founder
12:23
story section. So maybe we're not giving
12:24
it enough founder context and story
12:27
context in our initial brand context or
12:29
maybe it's just not inferring it
12:31
correctly. So what we would do is
12:32
actually provide specific feedback for
12:34
each of the outputs here and then copy
12:36
that back into claw code like more
12:38
founderled stories. Obviously that's
12:40
pretty shallow feedback right now. We
12:42
take that back to claw code and we would
12:45
say that and it would now start to
12:47
evaluate and improve the skill and tell
12:49
us what has changed from that skill. So
12:50
it's got it applying the fixes now with
12:52
extra emphasis on founder stories then
12:54
rerunning. Let me edit the skill.md. So
12:56
it's going to go and edit based on its
12:57
information it's found so far the
12:59
skill.md file. Now what we saw was we
13:01
can actually test things, AB test things
13:03
with or without the skill. So let's
13:06
split the terminal here.
13:08
Let's reopen up Claude and we can run a
13:10
simple AB test where we wanted to for
13:13
example test is the skill actually
13:14
improving the output versus not
13:16
improving the output. Can we create a
13:18
leaner version of the skill? So can we
13:19
strip out certain reference files that
13:21
aren't needed? And we effectively get
13:23
that sideby-side comparison of the
13:25
results of one versus the results of the
13:27
other. But it's also important here to
13:29
also specify the criteria that we're
13:31
marking against. So we want to know, you
13:33
know, which one takes longer, which one
13:34
has fewer tokens and which one ticks the
13:37
criteria in the persuasion toolkit or
13:39
ticks a classic persuasion framework the
13:41
most. So we would effectively ask it
13:42
something like create landing page copy
13:44
as an AB test with and without the
13:46
copywriting skill. That would run the
13:48
same set of evaluations. We give it a
13:50
bunch of criteria to mark against and we
13:52
then be able to see is the skill
13:53
actually adding to the quality or
13:54
reducing or taking away from the quality
13:56
and just costing us tokens. So
13:58
ultimately this is about improving our
13:59
skills in a quicker way than just
14:01
running our skills in production and
14:04
actually trying to work out what is and
14:06
isn't working. The eval function is
14:08
going to do that for us and make us
14:09
learn in quicker quicker loops. Like for
14:11
example, does the marketing copywriting
14:14
need these three reference files or can
14:16
we just work as well with one of them?
14:18
And you can see it's now it's rewriting
14:20
that copywriting skill so that we can
14:21
actually have an improved result and
14:23
it's running the evaluations again so we
14:25
can see the result of the new test which
14:26
is super powerful. Basically stop
14:28
guessing whether your skills actually
14:30
work. Test them with the anthropic skill
14:32
creator skill. Score them, improve them,
14:34
and that's how you go from a skill that
14:36
kind of works to one that's going to
14:38
nail it most of the time or 9 out of 10.
14:40
When you've got that 9 out of 10, you
14:42
can stop iterating on it. So there you
14:43
have it. four updates that genuinely
14:45
change what's possible with cloud code
14:47
loops for short-term automation.
14:49
Schedule tasks for daily and weekly
14:50
routines, Google workspace for further
14:53
access to your Google ecosystem, and
14:55
skills 2.0 for building skills that
14:56
actually are going to get better over
14:58
time. And speaking of skills that work
14:59
together, we've just launched a complete
15:01
agentic operating system built on claw
15:04
code that ties all of this into one
15:06
system, including all the skills you've
15:08
seen today. So, it's got brand memory,
15:10
18 production skills across marketing,
15:12
strategy, operations, and visual assets.
15:14
It's got a self-learning loop,
15:15
self-maintenance, and you can access it
15:17
from your phone through Telegram. So,
15:18
it's not a personal assistant. It's your
15:20
entire business context packaged into a
15:23
system that gets sharper every time you
15:25
use it. So, if you're in the academy,
15:26
you can download it right now and have
15:28
it running today. Links down below in
15:30
the description. And if you want to stay
15:31
on top of what's coming next, subscribe
15:33
and I'll keep breaking these down.
15:34
Thanks for watching. Please give it a
15:36
like and subscribe if you enjoyed the
15:37
content.
---
# video 4
En este video



Capítulos

Transcripción
Buscar en el video
Intro - Si le das una prompt vaga, te escupe basura
0:00
Abuela, salió video de gentleman. ¿Qué hace locura de mi corazón? Dios.
0:05
Impresionante. ¿Cómo andás, espectador mío? Mira, te voy a explicar una cosa. Si vos le tirás
0:11
una proma, bien a una gente de día que bueno, querés que le haga magia prácticamente, te va a escupir basura.
0:18
Es así no más. Entonces, después de qué te vas a quejar, ¿no? Si el problema no es la IA a, si no es que vos no le diste
0:24
un contexto. El problema también es el tema de darle tanto contexto. Acuérdense, cuanto más contexto damos,
El mito del "más contexto es mejor"
0:29
hay una cosa que se dice por ahí, es que mejor actúa una agente. Mentira. Hay que
0:34
darle lo justo y necesario. Bien. ¿Por qué? Porque todo el otro es ruido. Es algo que va a ofuscar el objetivo que
0:41
realmente queremos. Entonces, hoy les voy a mostrar cómo en Gentley hacemosd,
Qué es SDD y por qué no es prompt engineering
0:47
que es lo que se llama spec. Driven Development para que la gente no improvise nunca o por lo menos tratar un
0:53
poquitito. Es una forma de hacer un arnés bien a la hora de trabajar. Esto está hace bastante tiempo, desde antes
0:58
que se empiezan a llamar estas cosas arneses, pero bueno, esto no es prom engineering, esto directamente es ingeniería de proceso. Bien, entonces
1:05
vamos a verlo. Acá está el problema real. Cuando vos le pedís a un agente, "Implementame esto,
El problema: el agente no sabe tus tradeoffs ni constraints
1:12
locurísima, el agente no sabe qué patrón querés, qué tradeoffs ya descartaste, qué constraints tenés. que testing
1:19
strategy usas y tampoco la arquitectura que tenga sentido bien para tu proyecto.
1:24
Por ahí te da una resolución que está bastante buena, pero que no es lo que vos necesitas justo para este contexto que es tu proyecto. Bien, puede ser o tu
1:31
equipo o puede ser xazón. Un dev senior no le tira una tarea ambigua a otro dev y espera que adivine. Bien, menos vos,
1:39
locurísima, vos sabes quién sos. Bien, entonces por qué se lo hacemos así a la IA. Ese DDD se inspira. A ver, esto es
SDD se inspira en OpenSpec.dev pero va más lejos
1:46
viejísimo. Bien. lo mismo que el TDD, es viejísimo el test driven development, pero son metodologías que a la hora de
1:53
ser viejas eran tediosas de hacer, pero ahora con la IA es un limitador más, es
1:58
una forma de guiarla. Bien, entonces SD se inspira en lo que hace Openespec.Ded.D. Antes de implementar
2:04
voy a definir el cambio, voy a escribir lo que son los requerimientos, el diseño, las tareas, pero Gentil ahí lo
2:10
lleva más lejos que eso, porque el problema no es solamente tener un spec. Bien, el problema es que el agente
2:16
respeta el proceso, no se manda solo, no pierde contexto y puede verificar lo que
2:22
hizo. Resumen la tía. Ah, purísima. Vamos a ver por partes. Sí, antes de meternos en el flujo de SDD, hay un paso
El paso cero: SDD Init (calibrar antes de construir)
2:28
cero que la mayoría no conoce que se llama SDD Init. Esto no es parte del
2:33
cambio funcional, es la calibración del sistema antes de hacer SDD. ¿Qué es lo
2:39
que hace? Detecta el proyecto, lees y tenés un packet jason, un go.mod, un
2:44
pippo project.Tom, resumen, se fija las cosas del proyecto, qué estructura de carpetas tenés, qué frameworks,
2:50
convenciones, tooling, test, patrones existentes. Y antes de todo eso, el
2:56
arnés hace lo que se llama un preflight. ¿Qué es eso? Que te preguntas si querés trabajar de manera interactiva,
Preflight: interactivo o automático, dónde guardar
3:02
automática. En resumen, ¿querés que después de cada pasito yo te muestre lo
3:08
que hice? y vayamos ahí teando, te voy preguntando cosas y demás. ¿O queres que
3:13
yo haga todo? ¿Por qué? Es más. Bien. Entonces, después también te voy a preguntar dónde vamos a guardar las
3:18
cosas. Open spec, que directamente es una carpeta en el repositorio y ya queda ahí. O por ahí. Mirá, si tenés engram,
3:25
aguante, vas a poder guardar las cosas en engram, pero siempre guardando lo último que hacemos, ¿bien? No un
3:31
histórico, eso es para cosas rápidas y demás. Además, también te voy a preguntar, por ejemplo, cómo manejar
3:36
cuando el código ya es mucho, cuando es un PR grande, cuál es el presupuesto de review. Todo esto lo tenés en mi otro
3:43
video, que es el de 20 arneses que yo utilizo en gentelia. Bien, pero después
SDD Init aterriza en el proyecto: openspec config
3:48
de ese DD init aterriza eso en el proyecto. Crea o lee openspecfig.jamle,
3:56
guarda contexto del stack, reglas por fase y testing capabilities. Bien, y también otra cosa que hace que está
Skill Registry: índice de skills, no biblioteca gigante
4:02
bastante interesante es que verifica que exista el skill registry. ¿Qué es esto? Esto es, a ver, no es una biblioteca
4:09
gigante, sino es un índice de skills disponibles que tenemos tanto en el proyecto como también en el usuario.
4:16
Pero hay algo más y esto es importante. Detecta testing capabilities. Si encuentra test y un runner configurable
4:22
como puede ser, no sé, yo utilizo Vtest, buenísimo, utilizo Vitest browser, espectacular, que uso Playwrght o por
4:29
ahí. Todo eso lo detecta y lo deja identificado y también sabe qué scripts
4:35
utilizar para ejecutarlo. Bien, entonces ya en Tela ahí lo que va a hacer es activar lo que se llama el strictd mode.
4:41
¿Qué es eso? Es que en apply y verify el agente no trabaja en, bueno, impamente
Strict TDD mode: test primero, edge cases, evidencia
4:48
después vemos qué sucede, bien, sino que trabaja con una regla más fuerte. I test a runner, seguí test driven development.
4:57
Acepte primero los test antes de cualquier tipo de código para satisfacer los requerimientos. Después hago que
5:02
pasen y después le puse un tuning un poquitito bien de gentle ahí que es va a buscar casos edge. ¿Qué es eso? Casos
5:10
que pueden llegar a romper esa lógica y los va a cubrir también. Entonces todo
5:15
esto deja evidencia y hace que no se salte la verificación. Eseit es como calibrar la máquina antes de empezar a
5:22
cortar las piezas. Sí, no estás construyendo todavía, estás midiendo el proyecto, cargando contexto, detectando
5:29
test, preparando el arnés para que después el agente no improvise. Bien, espectacular. Acá, por ejemplo, tenemos
5:35
un proyecto, ¿ven? que es el de Gentlep y van a ver que tiene un open spec y cuando yo entro acá van a ver que
Ejemplo real: Gentle Pi y su config.yaml
5:41
tenemos un config y gam yamel, lo poner bien grande y este config y jamel es justamente el que denota que es el
5:48
proyecto, bien, todo lo que es el contexto te va a decir cuáles son las diferentes reglas a seguir. Sí, por
5:55
ejemplo, cuando hagas un apply tenés que utilizar este comando para hacer el testing, lo mismo para la parte de verificación. Eh, por ejemplo, también
6:03
necesita eh que cuando haga la fase te pregunte. Perfecto, lo tenemos ahí. Sí,
6:10
tenemos todo puesto. Ahí están todos los comandos, utilizar, todo. Esto está buenísimo. Sí, no más se los digo, es
6:16
espectacular. Pero te voy a mostrar otro conceptito más. Está también lo que es el skill registry, que esto es lo que yo
Skill Registry a fondo: el problema entre agentes
6:23
les decía antes, esto lo hice yo porque estaba harto de utilizar diferentes
6:28
agentes como puede ser Cloud Code, como Codex, como Gemini. lo que sea y que cada uno de ellos guarde las skills
6:34
donde se les canta y sea muy arduo tomarlo. ¿Vieron eso que ustedes dicen, "No, porque le pedí cada tal cosa, pero
6:41
no me usó la skill." Bueno, se terminó. Esto es una cosa que diferencia mucho a Gentle de cualquier otro setup que hayan
6:47
visto es cómo maneja el contexto. Bien, Gentil no le tira todas las skills completas a su vagente como si fuera una
6:53
bolsa de papa. Eso sería carísimo en Tokens y aparte metería ruido. Entonces, vamos a ver cómo se hace. Lo que hace el
7:00
orquestador es mucho más inteligente. Lee el skill registry del proyecto.
7:05
Detecta qué skills aplica según el contexto, que React, que Tycrip, que Go testing, que Playby, arquitectura, PR,
7:12
lo que corresponda. Pero ojo, el registry no es un resumen mágico ni un megaprompt, es un índice. El orquestador
El registry es un índice, el orquestador selecciona paths
7:19
selecciona los path exactos de las skills relevantes y se lo pasa a subagente. Entonces, el subagente no
7:26
recibe 20 documentos enormes, instrucciones que no aplican, directamente tiene un contrato claro
7:32
para esta tarea. Vas a tener que cargar estas skills y respetar estas reglas. Bien, eso lo que hace es reducir el
7:38
ruido, evita contexto innecesario, mantiene una separación importante y es que el orquestador coordina, el
7:45
subagente ejecuta y las skills siguen siendo la fuente de la verdad. Gender no
7:50
es un prom largo, es una orquestación que tiene un contexto seleccionado. Bien. Y viene una partecita que a mí me
7:58
encanta y ahora les voy a mostrar un ejemplito de todo esto, no se preocupen. Sí, hay una parte que es el presdd porque ya tenemos todo el sistema
Pre-SDD: la fase de research donde vos dirigís
8:04
calibrado, ya tenemos todo, pero viene la fase previa, ¿no? Que es donde vos como humano todavía estás dirigiendo de
8:11
cerca investigar el patrón e, por ejemplo, valor alternativas, armar un briefing técnico que después le entregas
8:17
al flujo CDD como input. Entonces, yo esto lo hago en terminal. Tengo un workflow donde abro documentos, rep de
8:25
proyecto, eh papers cuando aplica, bien, y voy armando un documento en mar con
8:30
los approachs considerados, los tradeoff, las decisiones preliminares, ese documento es lo que alimenta a la
8:37
exploración y al proposal dentro del Gentle Ei. ¿Sí? ¿Por qué hago esto antes de iniciar el flujo? Porque cuanto más
8:43
contexto entra en la arnés, mejor decide el agente en cada fase. Si vos ya hiciste la mitad de research, el agente
8:49
no tiene que adivinar y aparte reducimos gasto de tokens, pero de vuelta un contexto específico para el problema que
8:57
trato de solucionar. Sí, espectacular. Entonces, ahora lo que vamos a hacer es vamos a adentrarnos dentro de Gentle P,
9:03
que es el repositorio open source para configurar pi de gentli. Voy a abrir ahí
Entrando a Gentle Pi: 51 skills en el registry
9:08
y van a ver que va a ser una cosa muy interesante. Primero, es hermoso. Y segundo, ¿ven lo que dice acá? Skill
9:14
registry refresh. 51 skills. ¿Qué es lo que yo hago? Yo lo que hago es lo
9:19
siguiente. Dentro del proyecto voy a tener esta carpetita pun ATL. Cuando yo
9:25
introduzco mi persona dentro de la misma, van a ver que hay un skill registry MD. Y acá van a poder ver todas
9:33
las skills que está sacando, que son skills que yo tengo en configuraciones de Open Code, de Cla, de Gemini, Cursor,
9:40
Codex, Codeum, OpenCla, lo que dé. Bien. Y establezco el contrato de cómo tiene
9:48
que trabajar el orquestador y esto es solamente para la persona que delega. Bien, entonces acá tenemos todas las
9:54
skills en formato tabla donde vas a decir cuál es la skill, cuál es el
10:00
trigger que ejecuta dicha skill y después dónde la puede encontrar. Es así
10:05
de fácil, es un buscador. Esto cargarlo en contexto es baratísimo. Bien,
10:11
baratísimo. Y eso es lo que tratamos de hacer. Ahora que ya tenemos eso, voy a hacer otra cosa más. Le voy a pedir
Demo: mejoras de performance para iniciar Pi con SDD
10:17
algo. Quiero que con SDD eh hagamos mejoras para la performance a la hora de
10:25
iniciar Pi. Bien, vamos a ver qué pasa esto. Si va todo bien, primero buscan
10:31
engram si ya hay información sobre esto. Eso es otra cosa para otro día. Aguante Engram, gente. Aguante engram. Carga la
Engram busca contexto previo primero
10:36
skill de Gentlieli. Resumen, le da el contexto de cómo tiene que comportarse de todos los arneses y demás. empieza a
10:43
leer un poquitito las configuraciones, lee también el skill registry para saber qué skills hay y demás. Y con todo esto
10:50
me empieza a hacer las preguntas que yo les decía, el preflight, ¿quiero hacer interactivo o lo quiero hacer automático? Vamos a hacerlo interactivo.
10:58
¿Cómo lo quiero guardar? Que open spec o directamente lo dejamos en el chat o también puede ser engram, eh, lo que vos
11:03
quieras. Vamos a decir open spec. Y acá viene una parte importante. Si esto
11:09
empieza a ver que crece lo que es la cantidad de líneas, bien que va a cambiar. Si son más de lo que ahora
PRs encadenadas y auto-forecast
11:16
vamos a ver, te va a crear PRS encadenadas. Esto para otro día es una locura, bien, que se está haciendo ahora
11:22
mismo y que yo ya lo tengo integrado dentro de todo el ecosistema. Vamos a poner uno que es auto forecast, ¿qué
11:28
quiere decir? va a estimar el tamaño y si se pasa de el tamaño que le vamos a decir luego vamos a recibir una pregunta
11:34
diciendo cómo queremos no eh hacer un split de esas tareas y ahí está. Vamos a
11:40
ponerle unas 400 submit. ¿Ven cómo está todo integrado? Esto es hermoso. Esto va
11:46
actuando solito. Yo no tengo que hacer nada. Esto es divino. Y ahí es cuando empieza a explorar, hacer todas las
Cada step en un subagente para no ensuciar contexto
11:52
cosas que necesita hacer. Y cada uno de estos steps va a hacerse en un
11:58
subagente. ¿Para qué? Porque todo ese trabajo que va a hacer el agente no quiero que ensucie la conversación que
12:04
yo estoy teniendo con el orquestador. Entonces, esto, si yo ahora entro adentro, vemos todo lo que se le pasa a
12:11
ese subagente. En resumen, lo que le está pasando el orquestador al subagente para que este ejecute. Sí, le está
12:17
diciendo cómo es la ejecución. También le está diciendo información del proyecto, qué skills tiene que cargar,
12:23
que es lo que yo les decía. Por lo cual ni siquiera tienen que ir a leer el archivo de skills. Bien, el skill registry ya lo sabe. Después cuál es la
12:30
tarea que tiene ahí. Explorar solamente, no implementes porque esa es la parte más. Algunas cositas que yo también doy
12:37
para tratar de enfocarlo. Bien, y eso es un poquitito la fase que eh hacemos bien
12:44
dentro de lo que es SDD con Gendel y demás. Pero también no hay una fase de
Research y briefing (sponsor: Genspark)
12:49
research y briefing que es laburo. Hay días que lo hago a mano, otros que tengo
12:54
20 tas abiertos y todavía no escribí una sola línea de briefing. Entonces acá está el punto, ¿no? Cada día aparecen
13:00
herramientas nuevas que atacan esta fase específica. Hay gente que le gusta hacerlo, por ejemplo, con una sigl
13:06
directamente hablando. Como les digo, en esta parte interactiva de la exploración, podemos decirle, "Mira, para esta parte exploratoria, para
13:13
cuando tengas que hacer la proposal, bien, una vez que ya exploró todo, eso termina y con todo el contexto necesario
13:19
va a hacerte una propuesta. Esto es lo que podemos hacer. Entonces ahí tenés que hablar con él, investigar, hacer de
13:26
todo. Bien, pero como les digo, a mí me gusta también hacer una fase exploratoria previa a eso. Bien,
13:32
entonces se puede hacer por si se puede hacer con Wordpace visuales. Otras son extensiones del browser. Vos elegís la
13:38
que te baje la fricción según como vos trabajas. ¿Okay? Entonces, cuando se necesita, por ejemplo, acelerar la parte
13:44
del research estructurado y el briefing, una alternativa, por ejemplo, que está muy buena es la que te voy a mostrar
13:49
ahora. Antes de pasar a cóm Gentle convierte una proposal SD ejecutable, me voy a afeitar un poquitito. Bien,
13:55
después vamos a volver a la barba, pero quiero frenar un segundito. Esta sección la va a traer Jens Park, bien, avisito
Genspark AI Workspace: Deep Research
14:01
arriba, ya tú sabes, Ad, pero esto conecta directamente con lo que venimos viendo. Hay una fase de research que
14:08
define si la IA ejecuta bien o mal. La pregunta es justamente, ¿cómo bajas la fricción sin salteártela? Gin Park se
14:15
vende como un AI workspace All-inone que les voy a mostrar que tiene tres piezas que encadenan para esta fase y las tres
14:21
están pegadas justo con todo lo que ya venimos viendo. Vamos a empezar con lo primero. Lo primero que vamos a estar
14:27
viendo es esta interfaz. Esto es James Park AI Workspace. Está 4.0. Acá tenemos
14:32
todos los agentes. Puedes construir los tuyos también te puede crear imágenes, te puede crear videos, puede hacerlo de todo. Bien, pero les voy a mostrar cómo
14:39
podemos integrar herramientas a todo este flujo que ya venimos viendo para crear tus propios arneses y demás.
14:44
Entonces, hay una partecita acá que dice all agents. Yo lo toco y me voy a dar todos los agentes que ya vienen
14:49
configurados, pero también puedes crear los tuyos y vamos a hacer uno también. Pero el primero que vamos a estar viendo es justamente el de atentos con esto,
14:57
deep research. Van a ver que hay de todo, de creación de imágenes, videos, esto, el otro, hasta vos tenés de todo,
15:03
pero el que me importa a mí primero es el deep research. Bien, entonces acá vamos a hacer, por ejemplo, lo que sería
15:08
una investigación solo un poquitito de engram. Sí, Engram es mi modelo mental
15:14
para los agentes, para guardar contexto, que se puede compartir entre diferentes IDs y demás y está hecho en FT eh S5 con
15:22
un ranking justamente BM25 y además de eso es una base de datos SQLite local.
15:28
¿Para qué importa todo esto? Porque justamente le voy a preguntar que investigue cómo hacer eso. Justamente
15:33
con todo el stack que es con Go y demás. Le estoy diciendo qué es lo que necesito para la parte de research. Bien, con
15:40
todas las partes desde que se approches conocidos, bien para hacer esto tradeoff, o sea, ventajas y desventajas
15:46
y demás, riesgos comunes en producción, alternativas, no SQLite para ver justamente cómo podemos hacerlo,
15:52
decisiones comunes que toman proyectos similares y demás. Entonces, esto directamente ha ido, ha investigado en
15:57
profundidad el tema y miren cómo fue leyendo, ¿no?, diferentes documentaciones para llegar justamente a
16:04
este resultado con todas las cosas. Pero esto no queda acá. Además de que me va a
16:10
dar toda esta información, va a haber una parte interesantísima al final de todo. Miren, es mucha información, ¿eh?
16:16
Es impresionante para hacer justamente estas búsquedas que nosotros estábamos diciendo al principio que necesitamos saber para poder tomar decisiones. Y acá
16:23
lo tenemos. Hace lo que es una vista en la cual yo puedo entrar. Es más, esto se
16:28
puede descargar directamente en PDF. Puedes conectar un notion tuyo para poder guardar todo directamente ahí. Y acá tenemos cómo queda generado todo,
16:36
¿sí? Todo este briefing que recién les mostré, todo completito, pero nos vamos a quedar ahí. Vamos a ver ahora una
Convertir research en briefing técnico
16:42
segunda herramienta, otro segundo agente que tiene, que está buenísimo para poder transformar esto a algo presentable para
16:49
lo que es un equipo o como documentación propia, eh, no de repositorio. Entonces,
16:54
lo que voy a hacer ahora es tomar ese research que ya hicimos, ¿sí? y lo vamos a convertir en un briefing técnico con
17:00
headings, decision arquitectura, alternativas descartadas, formato claro, listo para utilizar. Bien, esta es la
17:05
idea. Entonces, acá lo tenemos. Le estoy diciendo toda esa parte. Le voy a decir que esto va a estar consumido para Spect
17:11
Dream and Development. Ya les estoy dando ahí una adelantito de lo que vamos a hacer y le estamos diciendo exactamente cómo queremos dicho
17:16
briefing. Ahora con esto directamente esto fue lo he hecho en HTML porque yo se lo pedí así. Ahí está todo y yo
17:23
cuando lo toque van a ver la implementación. Sí, ya es un documento que tiene un formato que está bonito,
17:29
está todo muy sexy. Ahora, esto también se puede presentar de diferentes maneras. Por ejemplo, por ejemplo,
17:35
podemos elegir acá diferentes eh digamos templates para poder hacer dicha
17:41
documentación. Así que esto está genial porque son todos cosas que ya están preparadas para ser funcionales y
17:46
productivas de una, sin tener que andar lidiando con las configuraciones custom y demás. Y ahora lo que vamos a hacer es poner new y podrían poner ustedes super
Creando un super agente custom para SDD
17:54
agent. ¿Para qué? para poder crear su propio agente. Ya tengo uno listo. Miren qué bonito. Genderd. Ahora vamos a ver
18:01
cómo se configuró y demás, pero literalmente ya acá puedo hacer lo que quiera, ¿sí? Ya puedo utilizarlo en el
18:08
día a día, pero vamos a ver cómo lo he creado directamente. Vamos a un poquito más de zoom. Le he dicho, quiero que me
18:15
crees un agente de especializado en estructurar documentaciones y demás de SDD. ¿Para qué? para desarrollo de eh
18:22
proyectos de software. Esta gente tiene que tomar cualquier tipo de input técnico y justamente sacar un draft de
18:29
todo el proceso de CD. Entonces, esto así no más se lo di, automáticamente ya lo creó. Miren qué bonito. Le puso un
18:37
diseño, le puso todo. Eh, esto está bastante interesante y todo se puede leer y se puede justamente actualizar.
18:43
Otra de las cosas que yo hice ahora es actualizarlo con un poco más de limonada. Sí, tenemos acá directamente
18:50
todas las especificaciones de metodologías, etcétera. Entonces, con esto, con reglas y demás, me dio la
18:56
última versión, que es esta. Sí. Entonces, otra cosa más. A su vez hice
19:02
una cosa bastante interesante. Bien, acá tenemos todos los pasos, todo muy bonito, todo explicadito, pero le pedí,
19:08
quiero que aparte crees documentos que son para ti, porque esto tiene como un AI Drive, bien, como Google Drive, pero
19:15
de IA para lo que son los agentes. Y le dije, quiero que guardes en documentaciones diferentes conceptos.
19:22
Cada uno de estos conceptos se puede utilizar luego para lo que es el entendimiento, el aprendizaje y demás.
19:27
De vuelta. Lazy loading de contexto. No queremos cargar todo de una, sino que lo haga de a poquitito. Bien. Y ahí está.
19:32
Automáticamente fue agregando cada uno de estos dentro, no sé si lo ven ahí, de
19:38
una base de datos que tiene directamente la herramienta. Sí. Lo bueno también tiene esto es que acá puedes seleccionar
Modelo Ultra: Opus 4.7 con 1M de contexto
19:44
qué tipo de pensamiento tiene y demás. Y tenemos el Ultra, por ejemplo, que es el Opus 47 con un millón de contexto. ¿Sí?
19:50
Entonces está bastante muy potente. Ahí lo tenemos. ya hizo toda la lo que es la estructura para estos archivos y demás.
19:57
Es superceto, no sé si lo ven. Eh, es realmente muy muy completo. Y ahora lo
20:02
que les voy a mostrar es cómo lo utilizo directamente. Yo lo hice acá porque ya lo tenía impuesto, pero podría haberlo
Briefing a preexecution de SDD
20:08
hecho directamente en una nueva directo para este agente. Y lo que hice fue decirle, "Mirá, procesá el siguiente
20:14
briefing técnico y genera la preexecution de SDD." Este es el briefing completo con toda la metodología. Pum. Esto, ¿saben qué? El
20:21
briefing que hicimos antes. Bien, el briefing público ese que yo les dije que
20:26
esto lo guarda acá y lo pueden exportar a Pf este mismo se lo he pasado y automáticamente fue, lo leyó e hizo
20:33
todo. Miren, acá está la proposal, estos son los riesgos, cómo ir para atrás,
20:38
bien cualquier cosa que suceda, el access criteria, resumen, todo lo que ya vimos de SD y que van a ver ahora
20:44
implementando, bien dentro de lo que es la terminal. Entonces, acá están todos los escenarios, están todas las partes
20:51
del proceso de SDD, los diseños, todo bien. Esto está bárbaro para poder hacer
20:56
este pensamiento y vemos de paso cómo se puede adaptar toda esta metodología que yo les estoy diciendo en diferentes
21:02
herramientas. Y ahora con esto volvamos al SSD por terminal, un ejemplo de lo que es la proposal. ¿Sí? Directamente te
Volvemos a terminal: la proposal
21:10
dice, "Dale, mira, la proposal está bien orientada, pero la idea central es esta, no arrancar optimizando a ciegas. Primero hacemos observar el arranque de
21:16
P con profiling opin. Resumen. Me está dando todo un resumen de todo lo que se quiere hacer. Se está hablando, por
21:22
ejemplo, no hay una lentitud en tal lado. Fantástico. Sospechoso principal es este. Ahí vamos a ver qué onda, cómo
21:28
se puede optimizar. A ver, esto no hay que optimizarlo, anda muy rápido. Esto ya está hilando en lo fino, pero para
21:34
que lo vean, sí, más o menos como está acá, por ejemplo, el punto discutible y dice la propósal dice considerar como
21:40
mucho una optimización chica. Eh, yo sería incluso más estricto para la primera PR. Bien, de todo. Entonces,
21:46
vamos a decir solo profiling, ¿les parece? Vamos con solo profiling. Eh,
Eligiendo scope: solo profiling para la primera PR
21:51
acá le podría decir, "Bueno, dime cómo vamos a hacer ese profiling. De todo." Sí, igualmente acá está un poquitito más
21:58
ya explicado arriba, pero para que vean cómo es. Ahora, una vez que esto ya se elige, esto ahora lo está guardando como
Guardando la decisión en Engram
22:04
una observación dentro de Engram. Mi cerebro de agente de vuelta es gratis también, es open source, es parte de
22:10
Genteli. Para cualquier cosa, yo el día de mañana vuelvo y digo, ¿qué estáamos haciendo con esto? Y lo sabe bien. No
22:16
perdemos contexto. Ahora crea un subagente nuevo donde se hacen las especificaciones que tienen que cubrir
22:22
dicha propuesta. Ahora cuando termine se los muestro. Ahora estamos acá directamente con la parte de specs ya
Subagente de specs: requisitos y escenarios
22:28
realizada. Ahí nos está diciendo, mira, este es el resumen de lo que se va a hacer. Si seguimos con el diseño, le voy
22:34
a pedir al subagente de diseño que defina cómo se va a implementar dichas funcionales a nivel técnico. De vuelta,
22:41
si yo voy entonces a la parte de open spec changes y veo la de improp startup
22:48
performance, esta es la que estamos hablando ahora mismo. Y si yo entro acá, vamos a ver que ya tenemos la proposal,
22:55
si la quieren ver en totalidad para poder hacer modificaciones o lo que ustedes necesitan y va a detallar cuál
23:01
es el problema, cuál es la intención, qué es lo que se va a meter dentro de esta propuesta, qué no se va a meter,
23:07
qué áreas se ven afectadas, en este caso qué archivos, bien, cuáles son las métricas que se quieren mejorar, cuáles
23:15
son los riesgos que hay que tener en cuenta. Rollback, ¿qué pasa si tenemos que volver para atrás? y también
23:20
obviamente un success criteria. Esto es lo que tiene que suceder para que esto funcione. Bien, asimismo ya tenemos la
23:28
parte de specs, en este caso la del scope chiquitito que acabamos de decir de profiling. ¿Ven? Como algo grande lo
23:35
empezamos a particionar en cosas más chiquititas. Perfecto. Entonces acá de vuelta va a decir cuáles son los
23:40
requisitos, cuáles son los escenarios, cuándo pase tal cosa. Entonces, bien,
23:45
esa es la idea. ¿Sí? Dado este caso, cuando pase tal cosa, entonces y tiene
23:51
que suceder esto de vuelta. Esto para cada tipo de requerimiento.
23:57
Esto es lo que nosotros necesitamos. ¿Para qué? Para la siguiente fase que vamos a ver qué es. Acá acaba de terminar lo que es el subente de diseño
Subagente de design: cómo implementar
24:04
y vamos a ver lo que dice. Design listo y delineado, solo profiling. Desiones principales. Se va a hacer un nuevo helper interno acá. Activación exacta es
24:12
esta. Esta es la salida del Jason. resumen, da toda la información de cómo quiere técnicamente desarrollar esa
24:19
especificación. ¿Sí? Entonces, ¿cuál es el tema de esta parte? Una vez que ya
24:25
tenemos todo esto, viene lo lindo, lo interesante. Vamos con las tareas. Y
24:31
mientras tanto, otra vez se los digo, pueden entrar, pueden entrar en cualquier momento a ver el diseño desde
24:38
acá mismo. Y ahí lo tenemos. Design Stata performance profiling only slice.
24:43
Y acá está de vuelta técnicamente todo como se quiere hacer. Miren, hasta da
24:49
recomendaciones de la API utilizar y demás. En resumen, tiene todo lo necesario para que cuando realmente se
24:55
tenga que hacer la implementación ya vaya con una guía específica de qué tocar, cómo tocarlo y mucho más. Esto es
25:03
super powerful. Y acá tenemos implementadas las tareas y lo va a hacer en unidades de trabajo. ¿Para qué? Para
Tareas en unidades de trabajo con checks
25:11
que se vaya haciendo de forma controlada. De nuevo, nosotros podemos entrar en lo que es el proyecto y vemos
25:16
la parte de tareas. Y acá van a ver que esto literalmente se va a ir metiendo con checks. ¿Sí? ¿Y por qué se hacen con
25:23
diferentes checks? Justamente para ir validando qué es lo que hace la IA. Y no solamente eso, sino dejando constancia
25:29
para que cualquier persona que quiera continuar este trabajo es la gente ya va a saber qué se hizo, cómo se hizo, por
25:35
qué se hizo y continuar sin ningún tipo de problema y más y me estés enrí no más. Ahora, antes de continuar, una
25:42
parte que me interesa que ustedes vean es cómo le pasó el trabajo a este
Apply: auto-forecast + strict TDD mode
25:47
subagente de apply. Bien, primero me va a decir justamente el tema del
25:52
autoforecast. ¿Para qué? para que me recomiende, e este trabajo se implementa de tal manera, vamos a ver qué onda,
25:57
hasta 400 líneas como mucho y demás, pero además de eso también tiene la parte de e modo estricto TDD está
26:05
activo. Eso quiere decir que tenés que utilizar PNPM test. Tenés que primero hacer las reglas como les decía, ¿no?
26:11
Los test en rojo, luego lo tenés que pasar a verde, luego tenés que triangular y refactorizar acorde y
26:18
justamente guardar todo tipo de evidencia. Bien, esto está espectacular,
26:24
gente. Esto es lo que yo les digo. Esto es un arnés. Esto realmente es un arnés.
26:30
Esto es lo de open spec, pero mejorado. Sí. El siguiente nivel, la evolución, el
26:36
ecosistema de gentilidad. ¡Carajo! Una vez que terminé de implementar, vino la etapa de revisión. Bien, para verificar.
Verify: encuentra problemas mayores y menores
26:43
Fíjense que cuando hizo la revisión sí que encontró cositas. Bien, dijo, todo
26:49
esto está correcto, no hay ningún problema, pero ojo con esto. Problema mayor, problema mayor, problema menor,
26:55
menor. Es cositas. En resumen, esto está fantástico. Por más que fuimos con toda
27:00
la guía, que fuimos todos bien, falta una parte de verificar. ¿Qué es lo que verifica? que las especificaciones
27:06
cumplan justamente al revés mejor, eh, que lo implementado cumpla con las especificaciones y con el diseño.
27:12
Entonces, una vez que terminó todo, llega a esta parte espectacular donde nos dice, "Hermoso de mi vida, listo, ya
27:19
ha hecho el apply, el review y el verify, ya está todo hecho." Bien, hubo
27:25
un problema, justamente hubo un gap de cobertura, que es lo que les dije recién, y cómo lo corregí. Acá está todo
27:32
hecho. ¿Qué faltaría? archivarlo. Bien, ahí le pongo, vamos con la siguiente fase a ver qué me dice. Y es cuando
Archive: documenta y conecta specs
27:37
inicia la parte de archivar. ¿Qué es esto? Archivar, va a documentar todo lo que me acaba de decir. Bien, lo va a
27:44
documentar y también va a buscar otros specs dentro de Open Spec que estén
27:50
relacionados a este para hacer esa conexión. Es decir, esto, por ejemplo, es una evolución de esto que ya hicimos
27:56
antes y demás y se empieza a crear como este histórico. Sí, pero este es el flujo completo de SD. y por qué es tan
28:03
importante. Entonces, vamos a ver que cuando entremos a proyecto va a pasar algo muy interesante. Entro Open Spec y
28:08
voy a ver que en la parte de cambios no está más. ¿Por qué? Porque ahora está archivado, ya ha terminado. Ahí lo
28:14
tenemos. Te pone la fecha cuando se terminó. Entro acá y tenemos la parte de especificaciones, la parte de profiling.
28:21
Y ahora sí que sí tenemos ya lo que sería el apply progress. Bien, es el reporte de todo, cómo se implementó y
28:28
demás. Después tenemos el reporte final. de todo, todo, todo, ya, cómo ha quedado
28:34
todo fantástico, se haga un warning, algo que haya quedado por ahí y también el state jamel, que va a ser un resumen
28:42
super rápido de todo lo que se fue configurando y demás para esta sesión y el verify report. Bien, ahí tenemos todo
28:50
explicadito y demás. Y esto sería si lo hiciéramos todo con Gentlei dentro de un
28:55
CLI, pero para que veas más o menos todo esto cómo funciona. Bien. Y la pregunta que se están haciendo entonces, ¿qué le
Recap: qué le agrega Gentle a OpenSpec.dev
29:01
agrega a Openp.d? Más o menos ya lo vimos, ¿no? Pero tenemos diferentes etapas. Uno es engram, es memoria
29:08
persistente. Cada fase guarda artefactos, el agente puede continuar sesiones sin perder el contexto y mucha
29:14
otras cosas más. Esto tengo un video de Eng, así que vayan a verlo porque es espectacular. Dos, el strict TDD mode.
29:20
Cuando hacemos el SD init, detectamos test la gente recibe instrucciones más fuertes en apply y verify, ¿no? Es
29:27
implemento y después los vemos. Acá hay test, hay runner, seguir el TDD, no te salte la verificación, etcétera. Tres,
29:35
sub agents por fase. Bien, ¿qué es esto? Que el orquestador no hace todo,
29:40
coordina. Una fase puede correr con un agente distinto que la siguiente, lo cual evita contaminar contexto y permite
29:47
usar modelos distintos por fase. Importante para no crear ruido a la hora de hacer esa implementación de
29:54
cualquiera de estas tareas, de cualquiera de estas fases. Bien, y la más importante de todas, la número cuatro, harnesses y Garels. Bien,
30:02
Gentley no confía en el agente, bien, no confía de que se porte todo bien y que
4. Harnesses: Gentle no confía, pone límites
30:07
sea un good boy. Bien, acá lo que le hace es le pone un arnesa alrededor antes de avanzar pregunta automático,
30:14
interactivo, dónde guardamos, qué hacemos, quién so qué acá qué hacemos si
30:20
supera el presupuesto, etcétera. Entonces, parece que es un detalle, pero no es un detalle porque el problema con
30:25
la IA, bien, con cualquier coding agent, no es que no sepa escribir código, es que si no le podés meter un límite hacen
30:33
cualquier cosa con muchísima confianza. Aparte y te lo van a decir, "No, es que esto es así, esto es espectacular." Y vos decís, "Pero no era así." Ah, tenés
30:40
razón. Te voy a decir, "Pero ya te exploté toda la base de datos." Entonces, Genti, convierte esos límites
30:45
en proceso de vuelta. No es prom engineering, es ingeniería de procesos, de workflows. Bien, entonces la
No es prompt engineering, es ingeniería de procesos
30:53
diferencia entre un dev junior con IA y un senior con no es la herramienta, es el contexto. El junior le pide magia,
Junior pide magia, senior dirige: Tony Stark y Jarvis
30:59
pero el senior lo dirige. Vos sos el arquitecto, la I es el ejecutor. Tony Stark no le dice a Jarvis, haceme algo
31:06
flaco. No le dice contexto, constraints, objetivos y feedback. Eso es gentil
31:12
aplicado a código o al cualquier cosa. Porque muchas me preguntan, esto lo puedo hacer con data science. Hacelo,
31:18
papurre, gente hasta con medicina que aplica esto. Bien. Y además, no pasa nada si sos junior, no pasa nada si
31:24
sosenior, si sos senior o lo que sea. Gentently te va a llevar ese objetivo que vos querés porque también tiene una
31:31
personalidad hecha para enseñar. Entonces, no tenga ningún tipo de problemática, lo instalo y veo que anda.
31:38
Sí. Entonces, tres cosas para cerrar. Una, si quieren que baje este flujo a una fichure real completa desde proceso
Cierre
31:45
hasta verify, déjenme en los comentarios si lo grabamos. Bien, a ver, acabo de hacer una presentación, pero si quier algo más lo hacemos y si no tienen mi
31:52
segundo canal Genteman Programming Bots BODS en el mismo YouTube y ahí hago
31:58
siempre streams todos los viernes explicando todos estos flujos implementando cosas en tiempo real.
32:04
Número dos, si estás armando un research técnico y querés probar una herramienta que ataques a fase específica, James
32:10
Park, como les mostré por ejemplo, le regala créditos gratis a registrarse. Tienen un link abajo en la descripción.
32:16
Y número tres, suscríbanse porque el próximo video seguimos con cómo hace que
32:21
los agentes trabajen en equipo, no como chatbots sueltos. Y no solamente eso, sino que también les doy novedades del
32:27
ambiente, cosas de seguridad y también enseño, obviamente, programación, soft skills, lo que quiera, papá. Acá
32:33
estamos. Así que nada, nos vemos. Lo van a compartir hasta con su abuela. Abuela. Saludo video de Gentman. Nos vemos,
32:40
gente hermosa. Chao. Nos vemos. Oh.

-> github:
- [https://github.com/Gentleman-Programming/Gentleman.Dots.git].
- [https://github.com/Gentleman-Programming/gentle-ai.git].
- [https://github.com/Gentleman-Programming/engram.git].
