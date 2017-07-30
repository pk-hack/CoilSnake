#!/usr/bin/python

import argparse
import os
import random
import sys

import Project
from coilsnake.util.common.yml import yml_load


sys.path.append('./')


def calcNewStat(statName, growthRates, newLevel, oldStatValue):
    r = 0
    if (statName == "Vitality" or statName == "IQ") and (newLevel <= 10):
        r = 5
    elif (newLevel % 4) == 0:
        r = random.randint(7, 10)
    else:
        r = random.randint(3, 6)

    statGain = ((growthRates[statName] * (newLevel-1)) - ((oldStatValue-2) * 10))
    statGain *= (r/50.0)

    return oldStatValue + int(statGain)


def calcStats(growthVars, endLevel):
    stats = [30, 10, 2, 2, 2, 2, 2, 2, 2]
    for i in range(2, endLevel+1):
        # Normal stats
        stats[2] = calcNewStat("Offense", growthVars, i, stats[2])
        stats[3] = calcNewStat("Defense", growthVars, i, stats[3])
        stats[4] = calcNewStat("Speed", growthVars, i, stats[4])
        stats[5] = calcNewStat("Guts", growthVars, i, stats[5])
        stats[6] = calcNewStat("Vitality", growthVars, i, stats[6])
        stats[7] = calcNewStat("IQ", growthVars, i, stats[7])
        stats[8] = calcNewStat("Luck", growthVars, i, stats[8])
        # HP
        newHP = 15 * stats[6]
        if (newHP - stats[0]) < 2:
            stats[0] += random.randint(1, 3)
        else:
            stats[0] = newHP
        # PP
        newPP = 5 * stats[7]
        if (newPP - stats[1]) < 2:
            stats[1] += random.randint(0, 2)
        else:
            stats[1] = newPP
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('levels', type=int,
                        metavar=('PC1_Level', 'PC2_Level', 'PC3_Level', 'PC4_Level'),
                        nargs=4, help='Party levels')
    parser.add_argument('projDir', metavar='ProjectDirectory', nargs=1,
                        help='CoilSnake project directory')
    parser.add_argument('--enemy', action='store', nargs=1,
                        metavar='Enemy_ID', type=int,
                        dest="enemyInfo", help="Enemy number")
    args = parser.parse_args()

    proj = Project.Project()
    proj.load(args.projDir[0] + os.sep + Project.PROJECT_FILENAME)

    partyStats = [None, None, None, None]
    with proj.get_resource("eb", "stats_growth_vars", "yml", "r") as f:
        growthVars = yml_load(f)
        for i in range(4):
            partyStats[i] = calcStats(growthVars[i], args.levels[i])
    
    print("*** Party Stats ***")
    print('\t'.join(map(str, ['', 'HP', 'PP', 'Off', 'Def', 'Speed', 'Guts', 'Vit', 'IQ', "Luck"])))
    for i in range(4):
        print(i, '\t', '\t'.join(map(str, partyStats[i])))
            
    if args.enemyInfo is not None:
        with proj.get_resource("eb", "enemy_configuration_table", "yml", "r") as f:
            enemyData = (yml_load(f))[args.enemyInfo[0]]
            print("\n*** Enemy Stats:", enemyData["Name"], "***")
            print('\t'.join(map(str, ['', 'HP', 'PP', 'Off', 'Def', 'Speed', 'Guts', "Luck"])))
            print('\t%d\t%d\t%d\t%d\t%d\t%d\t%d' % (enemyData["HP"], enemyData["PP"],
                                                    enemyData["Offense"], enemyData["Defense"],
                                                    enemyData["Speed"], enemyData["Guts"], enemyData["Luck"]))
            print("\n*** Damage Dealt by Enemy to Party ***")
            print("Level\tTarget\tMinDmg\tMaxDmg\tSMASH\tSmash%")
            for i in range(1, 5):
                for j in range(0, 4):
                    damage = i * enemyData["Offense"] - partyStats[j][3]
                    smashDamage = 4 * enemyData["Offense"] - partyStats[j][3]
                    smashOdds = enemyData["Guts"] / 5.0
                    print("%d\t%d\t%d\t%d\t%d\t%.2f%%" % (i, j, damage*0.75, damage*1.25, smashDamage, smashOdds))
                print()
            
            print("*** Damage Dealt by Party to Enemy ***")
            print("PC\tMinDmg\tMaxDmg\tSMASH\tSmash%")
            for i in range(0, 4):
                damage = 2 * partyStats[i][2] - enemyData["Defense"]
                smashDamage = 4 * partyStats[i][2] - enemyData["Defense"]
                smashOdds = max(partyStats[i][5] / 5.0, 5.0)
                print("%d\t%d\t%d\t%d\t%d" % (i, damage * 0.75, damage * 1.25, smashDamage, smashOdds))
                

if __name__ == '__main__':
    sys.exit(main())
